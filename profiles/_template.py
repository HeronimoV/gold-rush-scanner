"""Profile Template — Copy this file and customize for any industry.

To create a new profile:
1. Copy this file to profiles/your_industry.py
2. Fill in all the fields
3. Set INDUSTRY_PROFILE=your_industry as Railway env var (or in .env)
4. Redeploy — that's it

The scanner, dashboard, and all features automatically use the active profile.
"""

PROFILE_NAME = "Your Industry Name"
PROFILE_SLUG = "your_industry"

# Reddit subreddits to monitor
SUBREDDITS = []

# Local subreddits (require LOCAL_REQUIRED_TERMS match)
# Leave empty for nationwide scanning
LOCAL_SUBREDDITS = []
LOCAL_REQUIRED_TERMS = []

# Geographic targeting — cities/areas to boost score
# Leave empty for nationwide
TARGET_LOCATIONS = []
LOCATION_SCORE_BOOST = 0  # 0 = no boost, 3 = strong local preference

# Keywords and intent scores (1-10)
# 8-10: actively looking to buy/hire
# 6-7: researching/considering
# 3-5: general discussion
KEYWORDS = {}

# Skip posts containing these (obvious junk)
NEGATIVE_KEYWORDS = []

# Skip posts from sellers/advertisers (2+ matches = seller)
SELLER_SIGNALS = []

# Competitors to monitor for complaints (auto-score 10)
COMPETITORS = []
COMPETITOR_SUBREDDITS = []  # Where to look for competitor mentions

# YouTube search queries (requires YOUTUBE_API_KEY)
YOUTUBE_SEARCH_QUERIES = []

# Web forum search queries
WEB_SEARCH_QUERIES = []

# Craigslist regions (e.g. ["denver", "cosprings"])
# See https://www.craigslist.org/about/sites for region names
CRAIGSLIST_REGIONS = []

# Facebook groups to scan (requires APIFY_API_TOKEN)
FB_GROUPS = []

# Reply templates by intent level
REPLY_TEMPLATES = {
    "high": "Great question about {topic}! ...",
    "medium": "If you're looking into {topic}, ...",
    "low": "Interesting topic! {topic} is worth exploring. ...",
}
