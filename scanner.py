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

# Import location targeting if configured
try:
    from config import TARGET_LOCATIONS, LOCATION_SCORE_BOOST
except ImportError:
    TARGET_LOCATIONS = []
    LOCATION_SCORE_BOOST = 0

try:
    from config import LOCAL_SUBREDDITS, LOCAL_REQUIRED_TERMS
except ImportError:
    LOCAL_SUBREDDITS = []
    LOCAL_REQUIRED_TERMS = []

try:
    from config import NEGATIVE_KEYWORDS
except ImportError:
    NEGATIVE_KEYWORDS = []

try:
    from config import SELLER_SIGNALS
except ImportError:
    SELLER_SIGNALS = []


def _hits_negative_keyword(text_lower):
    """Check if text matches a negative keyword (obvious non-remodeling)."""
    return any(neg in text_lower for neg in NEGATIVE_KEYWORDS)


def _is_seller(text_lower):
    """Check if post is from a seller/advertiser (offering services, not seeking them)."""
    if not SELLER_SIGNALS:
        return False
    hits = sum(1 for s in SELLER_SIGNALS if s in text_lower)
    return hits >= 2


def _passes_local_filter(text, subreddit):
    """For local subreddits, require remodeling-related terms."""
    if subreddit not in LOCAL_SUBREDDITS:
        return True  # national subreddits pass through
    text_lower = text.lower()
    return any(term in text_lower for term in LOCAL_REQUIRED_TERMS)


def _is_colorado_relevant(text_lower, subreddit):
    """Check if a lead from a national subreddit is relevant to Colorado.
    
    Local subreddits are inherently Colorado — always relevant.
    National subreddits need either a Colorado location mention OR very high
    keyword specificity (score >= 7 without location boost).
    """
    if subreddit in LOCAL_SUBREDDITS:
        return True
    # Check if they mention Colorado
    if TARGET_LOCATIONS:
        for loc in TARGET_LOCATIONS:
            if loc in text_lower:
                return True
    return False  # national sub, no CO mention — will get score penalty
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


def _check_location(text_lower):
    """Check if text mentions a target location. Returns matched location or None."""
    if not TARGET_LOCATIONS:
        return None
    for loc in TARGET_LOCATIONS:
        if loc in text_lower:
            return loc
    return None


def score_text(text, subreddit=None):
    """Score text based on keyword matches + location boost. Returns (score, matched_keywords).
    
    For national subreddits without a Colorado mention, score is capped at 6
    (they can't be served by a CO-only contractor).
    """
    text_lower = text.lower()
    matches = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text_lower:
            matches.append((keyword, weight))
    if not matches:
        # Even with no keyword match, if they mention a target location in a
        # relevant subreddit, give it a base score
        location = _check_location(text_lower)
        if location and any(kw in text_lower for kw in ["remodel", "renovate", "contractor", "kitchen", "bathroom", "remodeler"]):
            return min(LOCATION_SCORE_BOOST + 3, 10), [(f"📍 {location}", LOCATION_SCORE_BOOST + 3)]
        return 0, []
    best = max(w for _, w in matches)
    bonus = min(len(matches) - 1, 2)
    score = best + bonus
    
    # Location boost — if post mentions a target location, boost the score
    location = _check_location(text_lower)
    if location:
        score += LOCATION_SCORE_BOOST
        matches.append((f"📍 {location}", LOCATION_SCORE_BOOST))
    elif subreddit and subreddit not in LOCAL_SUBREDDITS:
        # National sub, no Colorado mention — cap score (can't serve them)
        score = min(score, 6)
        matches.append(("⚠️ no CO location", 0))
    
    return min(score, 10), matches


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

    text_low = text.lower()

    # Skip obviously irrelevant posts
    if _hits_negative_keyword(text_low):
        return 0

    # Skip sellers/advertisers
    if _is_seller(text_low):
        return 0

    # Skip posts in local subreddits that aren't about remodeling
    if not _passes_local_filter(text, subreddit):
        return 0

    score, matches = score_text(text, subreddit)
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

    body_low = body.lower()

    # Skip obviously irrelevant comments
    if _hits_negative_keyword(body_low):
        return 0

    # Skip sellers/advertisers
    if _is_seller(body_low):
        return 0

    # Skip comments in local subreddits that aren't about remodeling
    if not _passes_local_filter(body, subreddit):
        return 0

    score, matches = score_text(body, subreddit)
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
    log.info("Social Prospector — Starting full scan")
    log.info(f"Subreddits: {len(SUBREDDITS)} | Keywords: {len(KEYWORDS)} | Min score: {MIN_SCORE_THRESHOLD}")
    log.info("=" * 50)

    total = 0
    for sub in SUBREDDITS:
        found = scan_subreddit(sub)
        total += found
        time.sleep(REQUEST_DELAY)

    import traceback as _tb

    # YouTube scan
    try:
        from youtube_scanner import run_youtube_scan
        yt_total = run_youtube_scan()
        total += yt_total
        log.info(f"YouTube: {yt_total} leads")
    except Exception as e:
        log.warning(f"YouTube scan skipped: {e}")

    # Web forum scan
    try:
        from web_scanner import run_web_scan
        import os
        brave_key = os.environ.get("BRAVE_API_KEY")
        web_total = run_web_scan(brave_key)
        total += web_total
        log.info(f"Web forums: {web_total} leads")
    except Exception as e:
        log.warning(f"Web scan error: {e}")
        _tb.print_exc()

    # Competitor complaint scan
    try:
        from competitors import run_competitor_scan
        comp_total = run_competitor_scan()
        total += comp_total
        log.info(f"Competitors: {comp_total} leads")
    except Exception as e:
        log.warning(f"Competitor scan error: {e}")
        _tb.print_exc()

    # Craigslist scan (local leads)
    try:
        from craigslist_scanner import run_craigslist_scan
        cl_total = run_craigslist_scan()
        total += cl_total
        log.info(f"Craigslist: {cl_total} leads")
    except Exception as e:
        log.warning(f"Craigslist scan error: {e}")
        _tb.print_exc()

    # Facebook groups scan
    try:
        from facebook_scanner import run_facebook_scan
        fb_total = run_facebook_scan()
        total += fb_total
        log.info(f"Facebook: {fb_total} leads")
    except Exception as e:
        log.warning(f"Facebook scan error: {e}")
        _tb.print_exc()

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
