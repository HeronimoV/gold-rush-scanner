#!/usr/bin/env python3
"""Craigslist scanner for local remodeling leads via Google/Brave search.

Craigslist blocks direct RSS from cloud servers, so we search for
Craigslist posts via search engines instead.
"""

import logging
import os
import re
import time
import requests
from datetime import datetime, timezone

from config import KEYWORDS, MIN_SCORE_THRESHOLD, REQUEST_DELAY, PROFILE_CRAIGSLIST_REGIONS
from db import insert_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("craigslist")

# Build search queries from profile regions
_regions = PROFILE_CRAIGSLIST_REGIONS or []
_region_names = {
    "denver": "Denver", "cosprings": "Colorado Springs", "boulder": "Boulder",
    "fortcollins": "Fort Collins", "pueblo": "Pueblo", "westslope": "Grand Junction",
    "highrockies": "High Rockies", "losangeles": "Los Angeles", "sfbay": "San Francisco",
    "chicago": "Chicago", "newyork": "New York", "seattle": "Seattle",
    "austin": "Austin", "dallas": "Dallas", "phoenix": "Phoenix",
}

# Generate search queries from regions + remodel terms
SEARCH_QUERIES = []
_search_terms = ["remodel", "contractor", "kitchen remodel", "bathroom remodel", "renovation", "handyman"]
for region in _regions[:4]:  # Limit to top 4 regions to avoid too many queries
    name = _region_names.get(region, region)
    for term in _search_terms[:3]:  # Top 3 terms per region
        SEARCH_QUERIES.append(f'site:{region}.craigslist.org "{term}"')
    # Also broader search
    SEARCH_QUERIES.append(f'site:craigslist.org "{name}" remodel OR contractor OR renovation')

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})


def search_brave(query, api_key):
    """Search via Brave API."""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": 15}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return [{"url": r["url"], "title": r.get("title", ""), "snippet": r.get("description", "")}
                for r in data.get("web", {}).get("results", [])]
    except Exception as e:
        log.debug(f"Brave search error: {e}")
        return []


def search_google(query):
    """Search Google and extract Craigslist results."""
    results = []
    try:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=15"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            links = re.findall(r'href="(https?://[a-z]+\.craigslist\.org/[^"]+)"', resp.text)
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text)
            for i, link in enumerate(links[:15]):
                title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
                results.append({"url": link, "title": title, "snippet": ""})
    except Exception as e:
        log.debug(f"Google search error: {e}")
    return results


def score_listing(text):
    """Score a Craigslist listing. +2 boost for being local."""
    text_lower = text.lower()
    matches = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text_lower:
            matches.append((keyword, weight))

    if not matches:
        return 5, [("📍 craigslist", 5)]

    best = max(w for _, w in matches)
    bonus = min(len(matches) - 1, 2)
    score = min(best + bonus + 2, 10)
    matches.append(("📍 craigslist", 2))
    return score, matches


def run_craigslist_scan():
    """Scan Craigslist via search engines."""
    if not SEARCH_QUERIES:
        log.info("Craigslist scan skipped — no regions configured in profile")
        return 0

    log.info(f"Scanning Craigslist via search ({len(SEARCH_QUERIES)} queries)...")
    total = 0
    seen_urls = set()
    brave_key = os.environ.get("BRAVE_API_KEY")

    for query in SEARCH_QUERIES:
        log.info(f"  CL search: {query[:60]}...")

        results = search_brave(query, brave_key) if brave_key else search_google(query)

        for r in results:
            url = r["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)

            content = f"{r['title']} {r['snippet']}".strip()
            if len(content) < 15:
                continue

            score, matches = score_listing(content)
            if score < MIN_SCORE_THRESHOLD:
                continue

            region_match = re.match(r'https?://([a-z]+)\.craigslist', url)
            region = region_match.group(1) if region_match else "unknown"
            region_label = _region_names.get(region, region).title()

            ts = datetime.now(timezone.utc).isoformat()
            inserted = insert_lead(
                "craigslist", f"cl/{region_label}", content[:2000],
                url, f"craigslist-{region}", score, ts,
            )
            if inserted:
                log.info(f"  Lead: cl/{region_label} (score={score})")
                total += 1

        time.sleep(REQUEST_DELAY + 1)

    log.info(f"Craigslist scan complete: {total} new leads")
    return total


if __name__ == "__main__":
    run_craigslist_scan()
