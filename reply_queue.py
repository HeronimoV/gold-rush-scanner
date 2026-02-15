"""Reddit reply approval queue with PRAW integration and rate limiting."""

import logging
import random
import threading
import time
from datetime import datetime, timezone

from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_USERNAME, REDDIT_PASSWORD,
)
from db import add_to_queue, get_queue_items, update_queue_status

log = logging.getLogger("reply_queue")

_reddit = None
_poster_thread = None
_poster_running = False


def _get_reddit():
    """Lazy-init PRAW Reddit instance."""
    global _reddit
    if _reddit is not None:
        return _reddit
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD]):
        return None
    try:
        import praw
        _reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent="GoldRushScanner/2.0 ReplyBot",
        )
        # Verify auth
        _reddit.user.me()
        log.info(f"Reddit authenticated as u/{REDDIT_USERNAME}")
        return _reddit
    except Exception as e:
        log.error(f"Reddit auth failed: {e}")
        _reddit = None
        return None


def reddit_configured():
    """Check if Reddit credentials are set."""
    return all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD])


def queue_reply(lead_id, reply_text, target_url):
    """Add a reply to the approval queue."""
    return add_to_queue(lead_id, reply_text, target_url)


def approve_reply(queue_id):
    """Mark a queued reply as approved (ready for posting)."""
    update_queue_status(queue_id, "approved")


def skip_reply(queue_id):
    """Skip a queued reply."""
    update_queue_status(queue_id, "skipped")


def post_reply(queue_id):
    """Post an approved reply to Reddit via PRAW."""
    from db import get_connection
    conn = get_connection()
    item = conn.execute("SELECT * FROM reply_queue WHERE id = ?", (queue_id,)).fetchone()
    conn.close()

    if not item:
        return False, "Queue item not found"

    reddit = _get_reddit()
    if not reddit:
        update_queue_status(queue_id, "failed", error="Reddit credentials not configured")
        return False, "Reddit credentials not configured"

    try:
        url = item["target_url"]
        reply_text = item["reply_text"]

        # Determine if it's a comment or post
        import praw
        if "/comments/" in url:
            # Extract the thing from URL
            submission = reddit.submission(url=url)
            # If URL has a specific comment ID (has extra path after post title)
            parts = url.rstrip("/").split("/")
            if len(parts) > 8 and parts[-2] not in ("comments",):
                # It's a comment permalink
                comment_id = parts[-1]
                comment = reddit.comment(id=comment_id)
                comment.reply(reply_text)
            else:
                # It's a post
                submission.reply(reply_text)

        now = datetime.now(timezone.utc).isoformat()
        from db import get_connection as gc
        conn = gc()
        conn.execute(
            "UPDATE reply_queue SET status = 'posted', posted_at = ?, error_message = '' WHERE id = ?",
            (now, queue_id),
        )
        conn.commit()
        conn.close()
        log.info(f"Posted reply #{queue_id} to {url}")
        return True, "Posted successfully"

    except Exception as e:
        update_queue_status(queue_id, "failed", error=str(e)[:500])
        log.error(f"Failed to post reply #{queue_id}: {e}")
        return False, str(e)


def _poster_loop():
    """Background thread: posts approved replies with rate limiting."""
    global _poster_running
    _poster_running = True
    while _poster_running:
        try:
            items = get_queue_items(status="approved", limit=1)
            if items:
                item = items[0]
                post_reply(item["id"])
                # Rate limit: 5 min + random 0-60s jitter
                delay = 300 + random.randint(0, 60)
                log.info(f"Rate limit: waiting {delay}s before next post")
                time.sleep(delay)
            else:
                time.sleep(30)  # Check every 30s when idle
        except Exception as e:
            log.error(f"Poster loop error: {e}")
            time.sleep(60)


def start_poster_thread():
    """Start the background poster thread (idempotent)."""
    global _poster_thread
    if _poster_thread and _poster_thread.is_alive():
        return
    _poster_thread = threading.Thread(target=_poster_loop, daemon=True, name="reply-poster")
    _poster_thread.start()
    log.info("Reply poster thread started")


def stop_poster_thread():
    global _poster_running
    _poster_running = False
