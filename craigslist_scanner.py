#!/usr/bin/env python3
"""Craigslist scanner for local remodeling leads in Colorado."""

import logging
import time
import requests
from datetime import datetime, timezone

from config import USER_AGENT, REQUEST_DELAY, KEYWORDS
from db import insert_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("craigslist")

# Colorado Craigslist regions
CRAIGSLIST_REGIONS = {
    "denver": "https://denver.craigslist.org",
    "cosprings": "https://cosprings.craigslist.org",
    "boulder": "https://boulder.craigslist.org",
    "fortcollins": "https://fortcollins.craigslist.org",
    "pueblo": "https://pueblo.craigslist.org",
    "westslope": "https://westslope.craigslist.org",
}

# Craigslist sections to scan
SECTIONS = [
    "/search/hss",   # household services
    "/search/rfs",   # real estate for sale (people buying fixer-uppers)
]

# Search terms for Craigslist
SEARCH_TERMS = [
    "remodel",
    "renovation",
    "kitchen remodel",
    "bathroom remodel",
    "contractor needed",
    "looking for contractor",
    "home improvement",
]

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})


def score_listing(title, text=""):
    """Score a Craigslist listing based on keywords."""
    combined = f"{title} {text}".lower()
    best_score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        if keyword in combined:
            matched.append((keyword, weight))
            if weight > best_score:
                best_score = weight
    if not matched:
        return 0, []
    bonus = min(len(matched) - 1, 2)
    return min(best_score + bonus, 10), matched


def scan_craigslist_region(region_name, base_url):
    """Scan a Craigslist region for remodeling-related posts using JSON API."""
    leads_found = 0
    
    for term in SEARCH_TERMS:
        try:
            # Use Craigslist search with JSON
            url = f"{base_url}/search/hhh?query={term.replace(' ', '+')}&format=rss"
            resp = session.get(url, timeout=15)
            
            if resp.status_code != 200:
                # Try regular HTML scraping as fallback
                url = f"{base_url}/search/hhh?query={term.replace(' ', '+')}"
                resp = session.get(url, timeout=15)
                
            if resp.status_code == 200:
                # Parse RSS/HTML for listings
                import re
                # Extract titles and links from RSS
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
                links = re.findall(r'<link>(https://[^<]+\.html)</link>', resp.text)
                
                if not titles:
                    # Try HTML parsing
                    titles = re.findall(r'class="result-title[^"]*"[^>]*>(.*?)</a>', resp.text)
                    links = re.findall(r'href="(https://[^"]+\.html)"[^>]*class="result-title', resp.text)
                
                for i, title in enumerate(titles[:20]):
                    title = title.strip()
                    if not title:
                        continue
                    link = links[i] if i < len(links) else f"{base_url}/search/hhh?query={term}"
                    
                    score, matches = score_listing(title)
                    if score < 4:
                        # Give a base score since they're actively searching Craigslist for this
                        score = max(score, 5)
                        matches = [(term, 5)]
                    
                    # Boost because it's LOCAL and on Craigslist (high intent)
                    score = min(score + 2, 10)
                    
                    ts = datetime.now(timezone.utc).isoformat()
                    inserted = insert_lead(
                        "craigslist", 
                        f"cl/{region_name}", 
                        title[:2000], 
                        link, 
                        f"craigslist-{region_name}", 
                        score, 
                        ts
                    )
                    if inserted:
                        match_str = ", ".join(k for k, _ in matches)
                        log.info(f"  Lead: cl/{region_name} (score={score}) — {match_str}")
                        leads_found += 1
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            log.warning(f"  Error scanning {region_name} for '{term}': {e}")
            continue
    
    return leads_found


def run_craigslist_scan():
    """Run a full Craigslist scan across all Colorado regions."""
    log.info(f"Scanning {len(CRAIGSLIST_REGIONS)} Craigslist regions...")
    total = 0
    
    for region, url in CRAIGSLIST_REGIONS.items():
        log.info(f"  Scanning Craigslist {region}...")
        found = scan_craigslist_region(region, url)
        total += found
        time.sleep(REQUEST_DELAY)
    
    log.info(f"Craigslist scan complete: {total} new leads")
    return total


if __name__ == "__main__":
    run_craigslist_scan()
