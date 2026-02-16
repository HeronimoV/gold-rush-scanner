#!/usr/bin/env python3
"""Monitor Reddit for competitor complaints — high-value leads."""

import logging
import time
import requests
from datetime import datetime, timezone

from config import SUBREDDITS, USER_AGENT, REQUEST_DELAY
from db import insert_lead, get_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("competitors")

# Competitors to monitor
COMPETITORS = [
    "Home Depot",
    "Lowes",
    "Angi",
    "Angie's List",
    "HomeAdvisor",
    "Thumbtack",
    "Houzz",
    "Bath Fitter",
    "Re-Bath",
    "Kitchen Magic",
    "Home Advisor",
]

# Complaint indicators — these signal someone is unhappy with their contractor/service
COMPLAINT_PHRASES = [
    "bad experience with",
    "terrible service from",
    "wouldn't recommend",
    "would not recommend",
    "don't hire",
    "do not hire",
    "awful experience",
    "horrible service",
    "ripped off by",
    "scam",
    "scammed by",
    "stay away from",
    "avoid",
    "worst contractor",
    "worst remodeler",
    "disappointed with",
    "never again",
    "overcharged",
    "poor customer service",
    "terrible experience",
    "charged me extra",
    "hidden fees",
    "bait and switch",
    "customer service nightmare",
    "regret hiring",
    "switching from",
    "fired my contractor",
    "done with",
    "fed up with",
    "frustrated with",
    "contractor ghosted",
    "contractor disappeared",
    "shoddy work",
    "poor workmanship",
    "cut corners",
    "not up to code",
    "failed inspection",
    "had to redo",
    "botched",
]

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def _check_competitor_complaint(text):
    """Check if text contains a competitor complaint. Returns (competitor, is_complaint, score)."""
    text_lower = text.lower()

    for competitor in COMPETITORS:
        comp_lower = competitor.lower()
        if comp_lower not in text_lower:
            continue

        # Check for complaint phrases near the competitor mention
        is_complaint = any(phrase in text_lower for phrase in COMPLAINT_PHRASES)

        if is_complaint:
            return competitor, True, 10  # Max score for competitor complaints
        else:
            # Competitor mentioned but not a complaint — still somewhat valuable
            return competitor, False, 6

    return None, False, 0


def _tag_lead_as_competitor(url, competitor, is_complaint):
    """Add competitor_complaint tag to the lead's notes."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, notes FROM leads WHERE url = ?", (url,)).fetchone()
        if row:
            existing_notes = row["notes"] or ""
            tag = f"competitor_complaint:{competitor}" if is_complaint else f"competitor_mention:{competitor}"
            if tag not in existing_notes:
                new_notes = f"{existing_notes} [{tag}]".strip()
                conn.execute("UPDATE leads SET notes = ? WHERE id = ?", (new_notes, row["id"]))
                conn.commit()
    finally:
        conn.close()


def search_subreddit_competitors(subreddit):
    """Search a subreddit for competitor mentions."""
    leads_found = 0

    # Search for each competitor
    for competitor in COMPETITORS:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": competitor,
            "restrict_sr": "on",
            "sort": "new",
            "limit": 25,
            "t": "week",
        }
        try:
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                continue
            children = resp.json().get("data", {}).get("children", [])

            for post in children:
                if post.get("kind") != "t3":
                    continue
                d = post["data"]
                author = d.get("author", "[deleted]")
                if author in ("[deleted]", "AutoModerator"):
                    continue

                title = d.get("title", "")
                selftext = d.get("selftext", "")
                text = f"{title} {selftext}".strip()
                permalink = d.get("permalink", "")
                created = d.get("created_utc", 0)

                comp, is_complaint, score = _check_competitor_complaint(text)
                if not comp:
                    continue

                post_url = f"https://reddit.com{permalink}"
                ts = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()

                inserted = insert_lead("reddit", author, text[:2000], post_url, subreddit, score, ts)
                if inserted:
                    _tag_lead_as_competitor(post_url, comp, is_complaint)
                    label = "🎯 COMPLAINT" if is_complaint else "mention"
                    log.info(f"Competitor {label}: {comp} by u/{author} in r/{subreddit} (score={score})")
                    leads_found += 1

        except Exception as e:
            log.warning(f"Error searching r/{subreddit} for {competitor}: {e}")

        time.sleep(REQUEST_DELAY)

    return leads_found


def run_competitor_scan():
    """Run competitor monitoring across all subreddits."""
    log.info("Starting competitor complaint scan...")
    log.info(f"Monitoring {len(COMPETITORS)} competitors across {len(SUBREDDITS)} subreddits")

    # Only scan the most relevant subreddits for competitor mentions (not all)
    try:
        from config import LOCAL_SUBREDDITS
        comp_subs = LOCAL_SUBREDDITS + ["HomeImprovement", "homeowners", "Renovations", "centuryhomes"]
    except ImportError:
        comp_subs = SUBREDDITS[:8]  # limit to first 8
    
    log.info(f"Monitoring {len(COMPETITORS)} competitors across {len(comp_subs)} subreddits")
    total = 0
    for sub in comp_subs:
        log.info(f"  Scanning r/{sub} for competitor mentions...")
        found = search_subreddit_competitors(sub)
        total += found
        time.sleep(REQUEST_DELAY)

    log.info(f"Competitor scan complete! {total} new leads found.")
    return total


def get_competitor_leads(limit=500):
    """Fetch leads tagged as competitor complaints."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM leads WHERE notes LIKE '%competitor_complaint:%' "
        "ORDER BY intent_score DESC, found_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_competitor_stats():
    """Get competitor-specific statistics."""
    conn = get_connection()
    complaints = conn.execute(
        "SELECT COUNT(*) as c FROM leads WHERE notes LIKE '%competitor_complaint:%'"
    ).fetchone()["c"]
    mentions = conn.execute(
        "SELECT COUNT(*) as c FROM leads WHERE notes LIKE '%competitor_mention:%'"
    ).fetchone()["c"]
    conn.close()
    return {"complaints": complaints, "mentions": mentions}


if __name__ == "__main__":
    run_competitor_scan()
