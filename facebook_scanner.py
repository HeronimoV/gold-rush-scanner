#!/usr/bin/env python3
"""Facebook Groups scanner for Colorado remodeling leads.

Supports two modes:
1. Apify API (recommended) — uses Apify's Facebook Groups Scraper actor
   Set APIFY_API_TOKEN in environment. Free tier gives 500 posts.
2. Google search fallback — searches Google for public FB group posts
   Less reliable but zero cost.

Facebook's Graph API no longer allows reading public group posts without
being an admin of the group, so we use these workarounds.
"""

import logging
import os
import re
import time
import requests
from datetime import datetime, timezone

from config import KEYWORDS, MIN_SCORE_THRESHOLD, REQUEST_DELAY
from db import insert_lead

# Import location/scoring helpers
try:
    from config import TARGET_LOCATIONS, LOCATION_SCORE_BOOST
except ImportError:
    TARGET_LOCATIONS = []
    LOCATION_SCORE_BOOST = 0

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("facebook")

# Colorado-specific Facebook groups to monitor
# These are public groups — URLs for Apify scraper
CO_FACEBOOK_GROUPS = [
    # Denver home improvement / remodeling
    "https://www.facebook.com/groups/denverHomeImprovement",
    "https://www.facebook.com/groups/DenverContractors",
    "https://www.facebook.com/groups/ColoradoHomeImprovement",
    "https://www.facebook.com/groups/DenverRealEstate",
    "https://www.facebook.com/groups/coloradospringsrealestate",
    "https://www.facebook.com/groups/FortCollinsHomeImprovement",
    "https://www.facebook.com/groups/BoulderHomeImprovement",
    # Neighborhood / community groups (remodel posts appear here)
    "https://www.facebook.com/groups/DenverNeighborhoods",
    "https://www.facebook.com/groups/AuroraCO",
    "https://www.facebook.com/groups/LakewoodCO",
    "https://www.facebook.com/groups/HighlandsRanchCO",
    "https://www.facebook.com/groups/CastleRockCO",
]

# Google search queries for Facebook group posts
GOOGLE_FB_QUERIES = [
    'site:facebook.com/groups "remodel" "Denver" OR "Colorado"',
    'site:facebook.com/groups "contractor" "Denver" OR "Colorado Springs"',
    'site:facebook.com/groups "kitchen remodel" "Colorado"',
    'site:facebook.com/groups "bathroom remodel" "Denver"',
    'site:facebook.com/groups "recommend a contractor" "Denver" OR "Colorado"',
    'site:facebook.com/groups "looking for contractor" "Denver" OR "Fort Collins" OR "Boulder"',
    'site:facebook.com/groups "home improvement" "Denver" OR "Colorado"',
    'site:facebook.com/groups "renovation" "Denver" OR "Colorado Springs"',
    'site:facebook.com/groups "handyman" "Denver" OR "Colorado"',
    'site:facebook.com/groups "basement finish" "Colorado"',
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})


def score_fb_post(text):
    """Score a Facebook post for remodeling intent."""
    text_lower = text.lower()
    matches = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text_lower:
            matches.append((keyword, weight))

    if not matches:
        # Base score for FB posts found via remodel search
        return 5, [("📘 facebook-CO", 5)]

    best = max(w for _, w in matches)
    bonus = min(len(matches) - 1, 2)
    # +2 boost for being local Colorado Facebook group
    score = min(best + bonus + 2, 10)

    # Location boost
    for loc in TARGET_LOCATIONS:
        if loc in text_lower:
            matches.append((f"📍 {loc}", LOCATION_SCORE_BOOST))
            score = min(score + LOCATION_SCORE_BOOST, 10)
            break

    matches.append(("📘 facebook", 0))
    return score, matches


def run_apify_scan(api_token):
    """Scan Facebook groups using Apify's Facebook Groups Scraper actor."""
    log.info(f"Scanning {len(CO_FACEBOOK_GROUPS)} Facebook groups via Apify...")
    total = 0

    # Start the actor run
    actor_id = "apify~facebook-groups-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"

    payload = {
        "startUrls": [{"url": url} for url in CO_FACEBOOK_GROUPS],
        "maxPosts": 50,  # per group
        "maxComments": 10,
        "sortBy": "CHRONOLOGICAL",  # most recent first
    }

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        log.info("  Starting Apify actor run...")
        resp = requests.post(run_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        run_data = resp.json().get("data", {})
        run_id = run_data.get("id")

        if not run_id:
            log.warning("  Failed to start Apify run")
            return 0

        # Poll for completion (max 5 minutes)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        for _ in range(30):  # 30 * 10s = 5 min
            time.sleep(10)
            status_resp = requests.get(status_url, headers=headers, timeout=15)
            status = status_resp.json().get("data", {}).get("status", "")
            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                log.warning(f"  Apify run {status}")
                return 0
            log.debug(f"  Apify run status: {status}")

        # Fetch results
        dataset_id = run_data.get("defaultDatasetId")
        if not dataset_id:
            log.warning("  No dataset ID from Apify run")
            return 0

        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        items_resp = requests.get(items_url, headers=headers, timeout=30)
        items = items_resp.json() if items_resp.status_code == 200 else []

        log.info(f"  Got {len(items)} posts from Apify")

        for item in items:
            text = item.get("text", "") or item.get("message", "") or ""
            post_url = item.get("url", "") or item.get("postUrl", "")
            author = item.get("userName", "") or item.get("user", {}).get("name", "fb-user")
            timestamp = item.get("time", "") or item.get("timestamp", "")
            group_name = item.get("groupName", "Facebook Group")

            if not text or len(text) < 15:
                continue

            score, matches = score_fb_post(text)
            if score < MIN_SCORE_THRESHOLD:
                continue

            ts = timestamp if timestamp else datetime.now(timezone.utc).isoformat()

            inserted = insert_lead(
                "facebook",
                author[:100],
                text[:2000],
                post_url or f"https://facebook.com/groups/{group_name}",
                f"fb/{group_name[:50]}",
                score,
                ts,
            )
            if inserted:
                match_str = ", ".join(k for k, _ in matches)
                log.info(f"  Lead: {author} in {group_name} (score={score}) — {match_str}")
                total += 1

            # Also check comments
            comments = item.get("topComments", []) or []
            for comment in comments:
                c_text = comment.get("text", "")
                c_author = comment.get("profileName", "fb-commenter")
                if not c_text or len(c_text) < 15:
                    continue
                c_score, c_matches = score_fb_post(c_text)
                if c_score < MIN_SCORE_THRESHOLD:
                    continue
                inserted = insert_lead(
                    "facebook",
                    c_author[:100],
                    c_text[:2000],
                    post_url or f"https://facebook.com/groups/{group_name}",
                    f"fb/{group_name[:50]}",
                    c_score,
                    ts,
                )
                if inserted:
                    total += 1

    except Exception as e:
        log.warning(f"  Apify scan error: {e}")

    return total


def run_google_fb_scan():
    """Fallback: Search Google for public Facebook group posts about remodeling in CO."""
    log.info(f"Scanning Facebook groups via Google search ({len(GOOGLE_FB_QUERIES)} queries)...")
    total = 0
    seen_urls = set()

    for query in GOOGLE_FB_QUERIES:
        try:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=15"
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                log.debug(f"  Google returned {resp.status_code}")
                time.sleep(REQUEST_DELAY * 2)
                continue

            # Extract Facebook links and snippets
            links = re.findall(r'href="(https?://(?:www\.)?facebook\.com/groups/[^"]+)"', resp.text)
            # Get text snippets near those links
            snippets = re.findall(r'<span[^>]*>([^<]{30,300})</span>', resp.text)

            for i, fb_url in enumerate(links[:15]):
                if fb_url in seen_urls:
                    continue
                seen_urls.add(fb_url)

                snippet = snippets[i] if i < len(snippets) else ""
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()

                if not snippet or len(snippet) < 20:
                    continue

                # Extract group name from URL
                group_match = re.search(r'groups/([^/?]+)', fb_url)
                group_name = group_match.group(1) if group_match else "unknown"

                score, matches = score_fb_post(snippet)
                if score < MIN_SCORE_THRESHOLD:
                    continue

                ts = datetime.now(timezone.utc).isoformat()
                inserted = insert_lead(
                    "facebook",
                    f"fb/{group_name}",
                    snippet[:2000],
                    fb_url,
                    f"fb/{group_name[:50]}",
                    score,
                    ts,
                )
                if inserted:
                    match_str = ", ".join(k for k, _ in matches)
                    log.info(f"  Lead: fb/{group_name} (score={score}) — {match_str}")
                    total += 1

        except Exception as e:
            log.debug(f"  Google FB search error: {e}")

        time.sleep(REQUEST_DELAY * 2)

    return total


def run_facebook_scan():
    """Run Facebook scan — Apify if token available, else Google fallback."""
    api_token = os.environ.get("APIFY_API_TOKEN")

    total = 0
    if api_token:
        total += run_apify_scan(api_token)
    else:
        log.info("No APIFY_API_TOKEN — using Google search fallback for Facebook groups")
        total += run_google_fb_scan()

    log.info(f"Facebook scan complete: {total} new leads")
    return total


if __name__ == "__main__":
    run_facebook_scan()
