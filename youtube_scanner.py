#!/usr/bin/env python3
"""YouTube comments scanner for gold/silver buying intent leads.

Requires a YouTube Data API v3 key (free).
Get one at: https://console.cloud.google.com/apis/credentials
1. Create a project (or use existing)
2. Enable "YouTube Data API v3"
3. Create an API key
4. Set YOUTUBE_API_KEY in config.py
"""

import logging
import time
import requests
from datetime import datetime, timezone

from config import (
    YOUTUBE_API_KEY, YOUTUBE_SEARCH_QUERIES,
    KEYWORDS, MIN_SCORE_THRESHOLD, REQUEST_DELAY,
)
from db import insert_lead
from scanner import score_text

log = logging.getLogger("youtube")

API_BASE = "https://www.googleapis.com/youtube/v3"


def search_videos(query, max_results=10):
    """Search YouTube for videos matching query. Requires API key."""
    if not YOUTUBE_API_KEY:
        return []
    resp = requests.get(f"{API_BASE}/search", params={
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "date",
        "key": YOUTUBE_API_KEY,
    }, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]


def get_comments(video_id, max_results=100):
    """Fetch top-level comments for a video. Requires API key."""
    if not YOUTUBE_API_KEY:
        return []
    comments = []
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(max_results, 100),
        "order": "relevance",
        "textFormat": "plainText",
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(f"{API_BASE}/commentThreads", params=params, timeout=15)
        resp.raise_for_status()
        for item in resp.json().get("items", []):
            snip = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": snip.get("authorDisplayName", "Unknown"),
                "text": snip.get("textDisplay", ""),
                "published": snip.get("publishedAt", ""),
                "video_id": video_id,
            })
    except Exception as e:
        log.warning(f"Error fetching comments for {video_id}: {e}")
    return comments


def process_youtube_comment(comment):
    """Score and save a YouTube comment if it meets threshold."""
    text = comment["text"]
    author = comment["author"]
    video_id = comment["video_id"]

    score, matches = score_text(text)
    if score >= MIN_SCORE_THRESHOLD:
        url = f"https://youtube.com/watch?v={video_id}"
        inserted = insert_lead(
            "youtube", author, text[:2000], f"{url}#comment-{hash(text) & 0xFFFFFF:06x}",
            "youtube", score, comment.get("published") or datetime.now(timezone.utc).isoformat(),
        )
        if inserted:
            log.info(f"YT Lead: {author} (score={score}) — {', '.join(k for k,_ in matches)}")
            return 1
    return 0


def run_youtube_scan():
    """Run YouTube comment scan across configured search queries."""
    if not YOUTUBE_API_KEY:
        log.info("YouTube scan skipped — no API key configured. Set YOUTUBE_API_KEY in config.py")
        return 0

    log.info("Starting YouTube comments scan...")
    total = 0
    seen_videos = set()

    for query in YOUTUBE_SEARCH_QUERIES:
        log.info(f"  Searching YouTube: '{query}'")
        try:
            video_ids = search_videos(query, max_results=5)
        except Exception as e:
            log.warning(f"  Search failed: {e}")
            continue

        for vid in video_ids:
            if vid in seen_videos:
                continue
            seen_videos.add(vid)
            time.sleep(REQUEST_DELAY)
            comments = get_comments(vid)
            for c in comments:
                total += process_youtube_comment(c)

    log.info(f"YouTube scan complete — {total} new leads")
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_youtube_scan()
