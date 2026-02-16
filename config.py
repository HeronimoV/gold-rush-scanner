"""Social Prospector — Dynamic Configuration Loader.

Loads industry profile from INDUSTRY_PROFILE env var.
Set INDUSTRY_PROFILE=remodeling_colorado or INDUSTRY_PROFILE=precious_metals
Default: remodeling_colorado

To add a new industry:
1. Copy profiles/_template.py to profiles/your_industry.py
2. Fill in keywords, subreddits, etc.
3. Set INDUSTRY_PROFILE=your_industry
4. Deploy — done.
"""

import os
import importlib

# --- Load active profile ---
_profile_name = os.environ.get("INDUSTRY_PROFILE", "remodeling_colorado")
try:
    _profile = importlib.import_module(f"profiles.{_profile_name}")
    print(f"📋 Loaded profile: {getattr(_profile, 'PROFILE_NAME', _profile_name)}")
except ImportError:
    print(f"⚠️ Profile '{_profile_name}' not found in profiles/, falling back to remodeling_colorado")
    _profile = importlib.import_module("profiles.remodeling_colorado")

# --- Industry-specific settings (from profile) ---
SUBREDDITS = getattr(_profile, "SUBREDDITS", [])
LOCAL_SUBREDDITS = getattr(_profile, "LOCAL_SUBREDDITS", [])
LOCAL_REQUIRED_TERMS = getattr(_profile, "LOCAL_REQUIRED_TERMS", [])
TARGET_LOCATIONS = getattr(_profile, "TARGET_LOCATIONS", [])
LOCATION_SCORE_BOOST = getattr(_profile, "LOCATION_SCORE_BOOST", 0)
KEYWORDS = getattr(_profile, "KEYWORDS", {})
NEGATIVE_KEYWORDS = getattr(_profile, "NEGATIVE_KEYWORDS", [])
SELLER_SIGNALS = getattr(_profile, "SELLER_SIGNALS", [])

# Optional profile fields used by other scanners
PROFILE_COMPETITORS = getattr(_profile, "COMPETITORS", [])
PROFILE_COMPETITOR_SUBREDDITS = getattr(_profile, "COMPETITOR_SUBREDDITS", [])
PROFILE_YOUTUBE_QUERIES = getattr(_profile, "YOUTUBE_SEARCH_QUERIES", [])
PROFILE_WEB_QUERIES = getattr(_profile, "WEB_SEARCH_QUERIES", [])
PROFILE_CRAIGSLIST_REGIONS = getattr(_profile, "CRAIGSLIST_REGIONS", [])
PROFILE_FB_GROUPS = getattr(_profile, "FB_GROUPS", [])
PROFILE_REPLY_TEMPLATES = getattr(_profile, "REPLY_TEMPLATES", {})
PROFILE_NAME = getattr(_profile, "PROFILE_NAME", _profile_name)

# --- Global settings (same for all profiles) ---
MIN_SCORE_THRESHOLD = 4
DB_PATH = "leads.db"

# Reddit JSON API
REDDIT_BASE_URL = "https://www.reddit.com"
USER_AGENT = "SocialProspector/2.0 (Lead Research Tool)"
REQUEST_DELAY = 2

# Dashboard
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000

# YouTube API key
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", None)

# YouTube search queries (profile overrides if set)
YOUTUBE_SEARCH_QUERIES = PROFILE_YOUTUBE_QUERIES or [
    "kitchen remodel before and after",
    "bathroom remodel ideas",
]

# Scheduler
SCAN_INTERVAL_HOURS = 2

# Email notifications
SMTP_HOST = os.environ.get("SMTP_HOST", None)
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", None)
SMTP_PASS = os.environ.get("SMTP_PASS", None)
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", None)

# Webhook
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", None)

# White-label
COMPANY_NAME = os.environ.get("COMPANY_NAME", "Social Prospector")
COMPANY_LOGO_URL = os.environ.get("COMPANY_LOGO_URL", None)
BRAND_COLOR = os.environ.get("BRAND_COLOR", "#daa520")

# Reddit API (PRAW)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", None)
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", None)
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", None)
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", None)
