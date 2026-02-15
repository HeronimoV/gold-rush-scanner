#!/usr/bin/env python3
"""Reddit scanner for gold/silver buying intent leads."""

import argparse
import logging
import time
import requests
from datetime import datetime, timezone

from config import (
    SUBREDDITS, KEYWORDS, MIN_SCORE_THRESHOLD,
    REDDIT_BASE_URL, USER_AGENT, REQUEST_DELAY, SCAN_INTERVAL_HOURS,
)
from db import insert_lead, is_lead_queued, add_to_queue, get_connection
from templates import generate_reply

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("scanner")

def _auto_queue_lead(author, content, subreddit, score, url):
    """Auto-queue a reply for high-intent leads."""
    if score < 7:
        return
    try:
        conn = get_connection()
        row = conn.execute("SELECT id FROM leads WHERE url = ?", (url,)).fetchone()
        conn.close()
        if not row:
            return
        lead_id = row["id"]
        if is_lead_queued(lead_id):
            return
        reply = generate_reply(author, content, subreddit, score)
        add_to_queue(lead_id, reply, url)
        log.info(f"Auto-queued reply for lead #{lead_id} (score={score})")
    except Exception as e:
        log.warning(f"Auto-queue failed: {e}")


session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def score_text(text):
    """Score text based on keyword matches. Returns (score, matched_keywords)."""
    text_lower = text.lower()
    matches = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text_lower:
            matches.append((keyword, weight))
    if not matches:
        return 0, []
    best = max(w for _, w in matches)
    bonus = min(len(matches) - 1, 2)
    return min(best + bonus, 10), matches


def fetch_subreddit(subreddit, sort="new", limit=50):
    url = f"{REDDIT_BASE_URL}/r/{subreddit}/{sort}.json?limit={limit}"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("children", [])
    except Exception as e:
        log.warning(f"Error fetching r/{subreddit}: {e}")
        return []


def fetch_comments(permalink):
    url = f"{REDDIT_BASE_URL}{permalink}.json?limit=100"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if len(data) > 1:
            return data[1].get("data", {}).get("children", [])
    except Exception as e:
        log.warning(f"Error fetching comments: {e}")
    return []


def extract_comments_flat(children):
    results = []
    for child in children:
        if child.get("kind") != "t1":
            continue
        d = child["data"]
        results.append(d)
        if d.get("replies") and isinstance(d["replies"], dict):
            nested = d["replies"].get("data", {}).get("children", [])
            results.extend(extract_comments_flat(nested))
    return results


def process_post(post_data, subreddit):
    title = post_data.get("title", "")
    selftext = post_data.get("selftext", "")
    text = f"{title} {selftext}".strip()
    author = post_data.get("author", "[deleted]")
    permalink = post_data.get("permalink", "")
    created = post_data.get("created_utc", 0)

    if author in ("[deleted]", "AutoModerator"):
        return 0

    score, matches = score_text(text)
    if score >= MIN_SCORE_THRESHOLD:
        url = f"https://reddit.com{permalink}"
        ts = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
        inserted = insert_lead("reddit", author, text[:2000], url, subreddit, score, ts)
        if inserted:
            log.info(f"Lead: u/{author} (score={score}) — {', '.join(k for k,_ in matches)}")
            _auto_queue_lead(author, text[:2000], subreddit, score, url)
            if score >= 8:
                try:
                    from notifications import notify_high_intent_lead
                    notify_high_intent_lead(author, subreddit, score, text[:500], url)
                except Exception as e:
                    log.warning(f"Notification failed: {e}")
            return 1
    return 0


def process_comment(comment_data, subreddit):
    body = comment_data.get("body", "")
    author = comment_data.get("author", "[deleted]")
    permalink = comment_data.get("permalink", "")
    created = comment_data.get("created_utc", 0)

    if author in ("[deleted]", "AutoModerator"):
        return 0

    score, matches = score_text(body)
    if score >= MIN_SCORE_THRESHOLD:
        url = f"https://reddit.com{permalink}"
        ts = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
        inserted = insert_lead("reddit", author, body[:2000], url, subreddit, score, ts)
        if inserted:
            log.info(f"Lead: u/{author} (score={score}) — {', '.join(k for k,_ in matches)}")
            _auto_queue_lead(author, body[:2000], subreddit, score, url)
            if score >= 8:
                try:
                    from notifications import notify_high_intent_lead
                    notify_high_intent_lead(author, subreddit, score, body[:500], url)
                except Exception as e:
                    log.warning(f"Notification failed: {e}")
            return 1
    return 0


def scan_subreddit(subreddit, check_comments=True):
    log.info(f"Scanning r/{subreddit}...")
    leads_found = 0

    posts = fetch_subreddit(subreddit, sort="new", limit=50)
    log.info(f"  Fetched {len(posts)} posts from r/{subreddit}")

    for post in posts:
        if post.get("kind") != "t3":
            continue
        d = post["data"]
        leads_found += process_post(d, subreddit)

        if check_comments:
            title = d.get("title", "").lower()
            if any(kw in title for kw in KEYWORDS):
                time.sleep(REQUEST_DELAY)
                comments = fetch_comments(d.get("permalink", ""))
                flat = extract_comments_flat(comments)
                for c in flat:
                    leads_found += process_comment(c, subreddit)

    time.sleep(REQUEST_DELAY)

    hot_posts = fetch_subreddit(subreddit, sort="hot", limit=25)
    for post in hot_posts:
        if post.get("kind") != "t3":
            continue
        d = post["data"]
        leads_found += process_post(d, subreddit)

    return leads_found


def run_full_scan():
    """Run a complete scan across all configured subreddits."""
    log.info("=" * 50)
    log.info("Gold Rush Scanner — Starting full scan")
    log.info(f"Subreddits: {len(SUBREDDITS)} | Keywords: {len(KEYWORDS)} | Min score: {MIN_SCORE_THRESHOLD}")
    log.info("=" * 50)

    total = 0
    for sub in SUBREDDITS:
        found = scan_subreddit(sub)
        total += found
        time.sleep(REQUEST_DELAY)

    # YouTube scan
    try:
        from youtube_scanner import run_youtube_scan
        yt_total = run_youtube_scan()
        total += yt_total
    except Exception as e:
        log.warning(f"YouTube scan skipped: {e}")

    log.info(f"Scan complete! {total} new leads found.")
    return total


def main():
    parser = argparse.ArgumentParser(description="Gold Rush Scanner")
    parser.add_argument("--loop", action="store_true", help=f"Run continuously every {SCAN_INTERVAL_HOURS} hours")
    args = parser.parse_args()

    if args.loop:
        log.info(f"Loop mode: scanning every {SCAN_INTERVAL_HOURS} hours. Ctrl+C to stop.")
        while True:
            try:
                run_full_scan()
            except Exception as e:
                log.error(f"Scan error: {e}")
            log.info(f"Sleeping {SCAN_INTERVAL_HOURS} hours...")
            time.sleep(SCAN_INTERVAL_HOURS * 3600)
    else:
        run_full_scan()


if __name__ == "__main__":
    main()
