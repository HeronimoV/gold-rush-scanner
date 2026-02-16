#!/usr/bin/env python3
"""Web search scraper for gold/silver buying discussions beyond Reddit."""

import logging
import time
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from config import KEYWORDS, MIN_SCORE_THRESHOLD, USER_AGENT, REQUEST_DELAY
from db import insert_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("web_scanner")

# Search queries for finding gold/silver buying discussions
SEARCH_QUERIES = [
    # Colorado-specific searches
    '"looking for a contractor" Denver remodel',
    '"need a remodeler" Colorado',
    '"recommend a contractor" Denver',
    '"kitchen remodel" Denver contractor',
    '"bathroom remodel" Colorado Springs',
    '"remodel" "Colorado" contractor recommendations',
    '"contractor recommendations" Boulder remodel',
    '"Fort Collins" remodel contractor',
    '"high end finishes" Denver renovation',
    '"luxury remodel" Colorado',
    # General (will catch CO mentions)
    '"looking for a contractor" remodel',
    '"need a remodeler" kitchen bathroom',
    '"how to find a good contractor" remodel',
]

# Known forums to target
KNOWN_FORUMS = {
    "houzz.com": "Houzz Forums",
    "diychatroom.com": "DIY Chat Room",
    "contractortalk.com": "Contractor Talk",
    "johnbridge.com": "John Bridge Tile Forum",
    "doityourself.com": "DoItYourself",
    "gardenweb.com": "Garden Web / Houzz",
    "thisoldhouse.com": "This Old House",
    "finehomebuilding.com": "Fine Home Building",
    "remodeling.hw.net": "Remodeling Magazine",
}

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})


def _identify_forum(url):
    """Identify the forum name from a URL."""
    domain = urlparse(url).netloc.lower().replace("www.", "")
    for forum_domain, forum_name in KNOWN_FORUMS.items():
        if forum_domain in domain:
            return forum_name
    return domain


def _score_text(text):
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


def search_google_scrape(query, num_results=20):
    """Scrape Google search results (fallback, no API key needed)."""
    import re as _re
    results = []
    if BeautifulSoup is None:
        # Fallback: use regex to parse Google results
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}&hl=en"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 200:
                links = _re.findall(r'href="(https?://(?!www\.google)[^"]+)"', resp.text)
                titles = _re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text)
                for i, href in enumerate(links[:num_results]):
                    title = _re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
                    results.append({"url": href, "title": title, "snippet": ""})
        except Exception as e:
            log.warning(f"Google search error: {e}")
        return results
    
    url = "https://www.google.com/search"
    params = {"q": query, "num": num_results, "hl": "en"}
    try:
        resp = session.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            log.warning(f"Google returned status {resp.status_code} for query: {query}")
            return results
        soup = BeautifulSoup(resp.text, "lxml")
        for g in soup.select("div.g"):
            link_tag = g.select_one("a[href]")
            title_tag = g.select_one("h3")
            snippet_tag = g.select_one("div.VwiC3b, span.aCOpRe, div[data-sncf]")
            if not link_tag or not title_tag:
                continue
            href = link_tag.get("href", "")
            if not href.startswith("http"):
                continue
            results.append({
                "title": title_tag.get_text(strip=True),
                "url": href,
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
            })
    except Exception as e:
        log.warning(f"Google scrape error for '{query}': {e}")
    return results


def search_brave_api(query, api_key=None, count=20):
    """Search using Brave Search API if API key is available."""
    if not api_key:
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": api_key}
    params = {"q": query, "count": count}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            })
        return results
    except Exception as e:
        log.warning(f"Brave API error: {e}")
        return []


def scrape_forum_page(url):
    """Try to scrape additional content from a forum page."""
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        # Try to extract post content
        for selector in ["div.post-content", "div.message-body", "article", "div.post", "div.postbody", "td.post"]:
            posts = soup.select(selector)
            if posts:
                return " ".join(p.get_text(strip=True)[:500] for p in posts[:3])
        # Fallback: get main content area
        main = soup.select_one("main, #content, .content, article")
        if main:
            return main.get_text(strip=True)[:1000]
    except Exception as e:
        log.debug(f"Could not scrape {url}: {e}")
    return None


def process_search_result(result):
    """Process a single search result and save if it's a lead."""
    title = result.get("title", "")
    url = result.get("url", "")
    snippet = result.get("snippet", "")

    if not url or not title:
        return 0

    # Skip non-forum/non-relevant results
    skip_domains = ["amazon.com", "ebay.com", "wikipedia.org", "youtube.com", "facebook.com", "twitter.com"]
    domain = urlparse(url).netloc.lower()
    if any(s in domain for s in skip_domains):
        return 0

    text = f"{title} {snippet}"
    score, matches = _score_text(text)

    if score < MIN_SCORE_THRESHOLD:
        return 0

    forum_name = _identify_forum(url)
    now = datetime.now(timezone.utc).isoformat()

    # Use forum name as "subreddit" field for consistency
    inserted = insert_lead("web", forum_name, text[:2000], url, forum_name, score, now)
    if inserted:
        log.info(f"Web lead: {forum_name} (score={score}) — {title[:80]}")
        return 1
    return 0


def run_web_scan(brave_api_key=None):
    """Run web search scan across all queries."""
    log.info("Starting web forum scan...")
    total = 0
    seen_urls = set()

    for query in SEARCH_QUERIES:
        log.info(f"  Searching: {query}")

        # Try Brave API first, fall back to Google scraping
        results = search_brave_api(query, brave_api_key)
        if not results:
            results = search_google_scrape(query)

        for result in results:
            url = result.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            total += process_search_result(result)

        time.sleep(REQUEST_DELAY * 2)  # Be polite with search engines

    # Also search specifically within known forums
    for forum_domain, forum_name in KNOWN_FORUMS.items():
        query = f"site:{forum_domain} remodel OR renovation OR contractor Colorado OR Denver"
        log.info(f"  Searching forum: {forum_name}")

        results = search_brave_api(query, brave_api_key)
        if not results:
            results = search_google_scrape(query)

        for result in results:
            url = result.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            total += process_search_result(result)

        time.sleep(REQUEST_DELAY * 2)

    log.info(f"Web scan complete! {total} new leads found.")
    return total


if __name__ == "__main__":
    import os
    brave_key = os.environ.get("BRAVE_API_KEY")
    run_web_scan(brave_key)
