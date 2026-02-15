"""Configuration for Gold/Silver Lead Scanner."""

# Subreddits to monitor
SUBREDDITS = [
    "Gold",
    "Silverbugs",
    "WallStreetSilver",
    "investing",
    "coins",
    "Bullion",
    "PreciousMetals",
    "personalfinance",
    "Pmsforsale",
    "goldbugs",
    "StackSilver",
]

# Keywords and their base intent weights (1-10)
# Higher weight = stronger buying intent
KEYWORDS = {
    # High intent (8-10): actively looking to buy
    "where to buy": 9,
    "best place to buy gold": 10,
    "best place to buy silver": 10,
    "first gold purchase": 9,
    "first silver purchase": 9,
    "recommend a dealer": 9,
    "trusted dealer": 9,
    "gold dealer": 8,
    "silver dealer": 8,
    "precious metals dealer": 8,
    "looking to buy": 9,
    "want to start stacking": 9,
    "where can i buy": 9,
    "how to buy gold": 8,
    "how to buy silver": 8,
    "should i buy gold": 8,
    "should i buy silver": 8,
    "thinking about buying": 8,
    "just bought my first": 8,
    "started collecting": 7,
    "best online dealer": 9,
    "cheapest gold": 8,
    "cheapest silver": 8,
    # Medium-high intent (6-7): considering buying
    "buying gold": 7,
    "buying silver": 7,
    "invest in gold": 7,
    "invest in silver": 7,
    "gold bars": 6,
    "gold coins": 6,
    "silver bars": 6,
    "silver coins": 6,
    "new to gold": 7,
    "new to silver": 7,
    "beginner gold": 7,
    "beginner silver": 7,
    "stack silver": 7,
    "stack gold": 7,
    "gold bullion": 6,
    "silver bullion": 6,
    "gold bar": 6,
    "silver bar": 6,
    "1 oz gold": 7,
    "1 oz silver": 7,
    "gold ira": 8,
    "silver ira": 8,
    "gold etf vs physical": 7,
    # Dealer mentions (6-7): researching specific dealers
    "apmex": 6,
    "jm bullion": 7,
    "sd bullion": 7,
    "money metals": 7,
    "local coin shop": 7,
    "lcs": 5,
    # Lower intent (3-5): general discussion
    "gold price": 4,
    "silver price": 4,
    "precious metals": 3,
    "gold market": 3,
    "silver market": 3,
}

# Minimum intent score to save a lead
MIN_SCORE_THRESHOLD = 4

# Database path
DB_PATH = "leads.db"

# Reddit JSON API settings
REDDIT_BASE_URL = "https://www.reddit.com"
USER_AGENT = "GoldRushScanner/2.0 (Lead Research Tool)"
REQUEST_DELAY = 2  # seconds between requests to be polite

# Dashboard settings
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000

# YouTube Data API v3 key (free — https://console.cloud.google.com/apis/credentials)
# Set to your API key string to enable YouTube scanning, or leave None to skip
YOUTUBE_API_KEY = None

# YouTube search queries
YOUTUBE_SEARCH_QUERIES = [
    "buying gold for beginners",
    "how to buy gold",
    "silver stacking",
    "gold investing 2025",
    "best gold dealers",
    "gold vs silver investment",
    "gold IRA",
    "physical gold buying guide",
]

# Scheduler
SCAN_INTERVAL_HOURS = 2
