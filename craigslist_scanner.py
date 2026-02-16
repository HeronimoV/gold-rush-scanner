#!/usr/bin/env python3
"""Craigslist scanner for local remodeling leads in Colorado.

Uses Craigslist's RSS feeds (XML) — no scraping needed, no rate limits.
Each Colorado city has its own Craigslist subdomain with categorized feeds.
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timezone
from html import unescape

from config import KEYWORDS, MIN_SCORE_THRESHOLD, REQUEST_DELAY, PROFILE_CRAIGSLIST_REGIONS
from db import insert_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("craigslist")

# All known Craigslist regions (used for lookup)
ALL_REGIONS = {
    "denver": "denver", "cosprings": "cosprings", "boulder": "boulder",
    "fortcollins": "fortcollins", "pueblo": "pueblo",
    "westslope": "westslope", "highrockies": "highrockies",
    # Add more as needed for other states
    "losangeles": "losangeles", "sfbay": "sfbay", "chicago": "chicago",
    "newyork": "newyork", "seattle": "seattle", "austin": "austin",
    "dallas": "dallas", "houston": "houston", "phoenix": "phoenix",
    "atlanta": "atlanta", "miami": "miami", "boston": "boston",
    "portland": "portland", "sandiego": "sandiego",
}

# Active regions from profile (or default Colorado)
CO_REGIONS = {}
_profile_regions = PROFILE_CRAIGSLIST_REGIONS or ["denver", "cosprings", "boulder", "fortcollins", "pueblo", "westslope", "highrockies"]
for _r in _profile_regions:
    CO_REGIONS[_r] = ALL_REGIONS.get(_r, _r)

# Craigslist categories where remodeling leads appear
# Format: (category_path, category_name)
CATEGORIES = [
    # Housing — people looking for home services
    ("search/hhh", "housing"),
    # Services — people requesting contractor work
    ("search/bbb", "services"),
    # Gigs — people posting remodel gigs/jobs
    ("search/ggg", "gigs"),
    # For Sale > Materials — people buying remodel materials (might need contractor)
    ("search/mat", "materials"),
]

# Search terms — keep concise to avoid too many RSS calls
# 7 regions × 4 categories × N terms = lots of requests
SEARCH_TERMS = [
    "remodel",
    "renovation",
    "contractor",
    "kitchen",
    "bathroom",
    "basement",
    "handyman",
    "home improvement",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; SocialProspector/2.0)",
    "Accept": "application/rss+xml, application/xml, text/xml",
})

# Namespace for Craigslist RSS
RDF_NS = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
RSS_NS = {
    "": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "enc": "http://purl.oclc.org/net/rss_2.0/enc#",
}


def _clean_html(text):
    """Strip HTML tags and decode entities."""
    text = unescape(text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def score_listing(text):
    """Score a Craigslist listing. Returns (score, matched_keywords).
    
    Craigslist Colorado posts get a +2 base boost since they're inherently local.
    """
    text_lower = text.lower()
    matches = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text_lower:
            matches.append((keyword, weight))

    if not matches:
        # If we found it via remodel search term, give base score
        return 5, [("📍 craigslist-CO", 5)]

    best = max(w for _, w in matches)
    bonus = min(len(matches) - 1, 2)
    # +2 boost for being a local Colorado Craigslist post
    score = min(best + bonus + 2, 10)
    matches.append(("📍 craigslist-CO", 2))
    return score, matches


def fetch_rss_feed(region, category_path, search_term):
    """Fetch a Craigslist RSS feed for a specific region/category/search."""
    subdomain = CO_REGIONS[region]
    # Craigslist RSS feed URL format
    url = f"https://{subdomain}.craigslist.org/{category_path}?format=rss&query={requests.utils.quote(search_term)}&sort=date"

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 404:
            return []  # Category doesn't exist in this region
        if resp.status_code != 200:
            log.debug(f"  RSS {resp.status_code} for {subdomain}/{category_path}?q={search_term}")
            return []
        return parse_rss(resp.text, region)
    except Exception as e:
        log.debug(f"  RSS error {subdomain}/{category_path}: {e}")
        return []


def parse_rss(xml_text, region):
    """Parse Craigslist RSS XML into listings."""
    items = []
    try:
        root = ET.fromstring(xml_text)

        # Try RSS 2.0 format first
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            date_el = item.find("dc:date", {"dc": "http://purl.org/dc/elements/1.1/"})
            if date_el is None:
                date_el = item.find("pubDate")

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.text.strip() if link_el is not None and link_el.text else ""
            desc = _clean_html(desc_el.text) if desc_el is not None and desc_el.text else ""
            date = date_el.text.strip() if date_el is not None and date_el.text else ""

            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "description": desc,
                    "date": date,
                    "region": region,
                })

        # Try RDF/RSS 1.0 format (older Craigslist format)
        if not items:
            ns = "http://purl.org/rss/1.0/"
            for item in root.findall(f".//{{{ns}}}item"):
                title_el = item.find(f"{{{ns}}}title")
                link_el = item.find(f"{{{ns}}}link")
                desc_el = item.find(f"{{{ns}}}description")
                date_el = item.find("{http://purl.org/dc/elements/1.1/}date")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                desc = _clean_html(desc_el.text) if desc_el is not None and desc_el.text else ""
                date = date_el.text.strip() if date_el is not None and date_el.text else ""

                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "description": desc,
                        "date": date,
                        "region": region,
                    })
    except ET.ParseError as e:
        log.debug(f"  XML parse error: {e}")
    return items


def process_listing(listing):
    """Score and save a Craigslist listing as a lead."""
    title = listing["title"]
    desc = listing.get("description", "")
    url = listing["url"]
    region = listing["region"]
    date_str = listing.get("date", "")

    content = f"{title} {desc}".strip()
    if len(content) < 15:
        return 0

    score, matches = score_listing(content)
    if score < MIN_SCORE_THRESHOLD:
        return 0

    # Parse date or use now
    try:
        if date_str:
            ts = date_str  # Already ISO format from Craigslist
        else:
            ts = datetime.now(timezone.utc).isoformat()
    except Exception:
        ts = datetime.now(timezone.utc).isoformat()

    region_label = region.replace("cosprings", "CO Springs").replace("fortcollins", "Fort Collins").replace("westslope", "W. Slope").replace("highrockies", "High Rockies").title()

    inserted = insert_lead(
        "craigslist",
        f"cl/{region_label}",
        content[:2000],
        url,
        f"craigslist-{region}",
        score,
        ts,
    )
    if inserted:
        match_str = ", ".join(k for k, _ in matches)
        log.info(f"  Lead: cl/{region_label} (score={score}) — {match_str}")
        return 1
    return 0


def run_craigslist_scan():
    """Run Craigslist scan across all Colorado regions."""
    log.info(f"Starting Craigslist scan — {len(CO_REGIONS)} regions, {len(CATEGORIES)} categories, {len(SEARCH_TERMS)} search terms")
    total = 0
    seen_urls = set()

    for region in CO_REGIONS:
        region_leads = 0
        for cat_path, cat_name in CATEGORIES:
            for term in SEARCH_TERMS:
                listings = fetch_rss_feed(region, cat_path, term)
                for listing in listings:
                    if listing["url"] in seen_urls:
                        continue
                    seen_urls.add(listing["url"])
                    region_leads += process_listing(listing)
                time.sleep(0.5)  # Light delay between RSS requests
            time.sleep(REQUEST_DELAY)

        if region_leads:
            log.info(f"  {region}: {region_leads} new leads")
        total += region_leads

    log.info(f"Craigslist scan complete: {total} new leads from {len(seen_urls)} listings checked")
    return total


if __name__ == "__main__":
    run_craigslist_scan()
