#!/usr/bin/env python3
"""Craigslist scanner for local remodeling leads in Colorado via Google search."""

import logging
import re
import time
import requests
from datetime import datetime, timezone

from config import USER_AGENT, REQUEST_DELAY, KEYWORDS
from db import insert_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("craigslist")

# Search Craigslist via Google (Craigslist blocks direct scraping)
CRAIGSLIST_SEARCHES = [
    'site:craigslist.org "remodel" denver OR "colorado springs" OR boulder OR "fort collins"',
    'site:craigslist.org "kitchen remodel" colorado',
    'site:craigslist.org "bathroom remodel" colorado',
    'site:craigslist.org "contractor needed" denver OR colorado',
    'site:craigslist.org "looking for contractor" denver OR colorado',
    'site:craigslist.org "renovation" denver OR "colorado springs"',
    'site:craigslist.org "home improvement" denver colorado',
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})


def search_google(query):
    """Search Google and extract results."""
    results = []
    try:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=15"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            # Extract titles and URLs from Google results
            # Look for Craigslist links
            links = re.findall(r'href="(https?://[a-z]+\.craigslist\.org/[^"]+)"', resp.text)
            titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text)
            snippets = re.findall(r'<span class="[^"]*">([^<]{50,300})</span>', resp.text)
            
            for i, link in enumerate(links[:15]):
                title = titles[i] if i < len(titles) else ""
                snippet = snippets[i] if i < len(snippets) else ""
                # Clean HTML tags from title
                title = re.sub(r'<[^>]+>', '', title).strip()
                if title or snippet:
                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet,
                    })
    except Exception as e:
        log.warning(f"Google search error: {e}")
    return results


def score_listing(title, snippet=""):
    """Score a listing based on keywords."""
    combined = f"{title} {snippet}".lower()
    best_score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        if keyword in combined:
            matched.append((keyword, weight))
            if weight > best_score:
                best_score = weight
    if not matched:
        # Base score for Craigslist results (they searched for remodel terms)
        return 6, [("craigslist-remodel", 6)]
    bonus = min(len(matched) - 1, 2)
    # Boost for being local Craigslist
    return min(best_score + bonus + 2, 10), matched


def run_craigslist_scan():
    """Scan Craigslist Colorado via Google search."""
    log.info(f"Scanning Craigslist via Google ({len(CRAIGSLIST_SEARCHES)} queries)...")
    total = 0
    seen_urls = set()
    
    for query in CRAIGSLIST_SEARCHES:
        results = search_google(query)
        log.info(f"  Found {len(results)} results for: {query[:60]}...")
        
        for r in results:
            url = r["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = r["title"]
            snippet = r["snippet"]
            content = f"{title} {snippet}".strip()
            
            if not content or len(content) < 10:
                continue
            
            score, matches = score_listing(title, snippet)
            
            # Extract region from URL
            region_match = re.match(r'https?://([a-z]+)\.craigslist', url)
            region = region_match.group(1) if region_match else "colorado"
            
            ts = datetime.now(timezone.utc).isoformat()
            inserted = insert_lead(
                "craigslist",
                f"cl/{region}",
                content[:2000],
                url,
                f"craigslist-{region}",
                score,
                ts
            )
            if inserted:
                match_str = ", ".join(k for k, _ in matches)
                log.info(f"  Lead: cl/{region} (score={score}) — {match_str}")
                total += 1
        
        time.sleep(REQUEST_DELAY + 1)  # extra delay for Google
    
    log.info(f"Craigslist scan complete: {total} new leads")
    return total


if __name__ == "__main__":
    run_craigslist_scan()
