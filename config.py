"""Configuration for Social Prospector — Home Remodeling & High-End Finishes."""

# Subreddits to monitor — National + Colorado-specific
SUBREDDITS = [
    # Colorado local subreddits
    "Denver",
    "Colorado",
    "ColoradoSprings",
    "FortCollins",
    "Boulder",
    "AuroraCO",
    "Lakewood",
    "Pueblo",
    "GrandJunction",
    "Longmont",
    "Loveland",
    "Greeley",
    "Arvada",
    "Westminster",
    "Thornton",
    "Centennial",
    "Broomfield",
    "CastleRock",
    # National (will filter for CO mentions)
    "HomeImprovement",
    "HomeRenovation",
    "Remodeling",
    "InteriorDesign",
    "kitchenremodel",
    "BathroomRemodel",
    "DIY",
    "homeowners",
    "RealEstate",
    "firsttimehomebuyer",
    "centuryhomes",
    "Renovations",
    "Contractors",
]

# Location targeting — Colorado cities and areas
# Posts mentioning these get a score boost
TARGET_LOCATIONS = [
    "denver", "colorado springs", "aurora", "fort collins", "lakewood",
    "thornton", "arvada", "westminster", "pueblo", "centennial",
    "boulder", "greeley", "longmont", "loveland", "broomfield",
    "castle rock", "parker", "commerce city", "littleton", "northglenn",
    "brighton", "englewood", "wheat ridge", "golden", "erie",
    "lafayette", "louisville", "superior", "firestone", "frederick",
    "dacono", "highlands ranch", "lone tree", "cherry creek",
    "stapleton", "wash park", "capitol hill", "lodo", "rino",
    "five points", "park hill", "sloan lake", "congress park",
    "colorado", "front range", "springs", "co springs",
    "denvr",  # common misspelling
]
LOCATION_SCORE_BOOST = 3  # boost score by this much if location detected

# Keywords and their base intent weights (1-10)
# Higher weight = stronger buying intent
KEYWORDS = {
    # High intent (8-10): actively looking for a contractor/remodeler
    "looking for a contractor": 10,
    "need a contractor": 10,
    "recommend a contractor": 10,
    "looking for a remodeler": 10,
    "need a remodeler": 10,
    "recommend a remodeler": 10,
    "who did your remodel": 9,
    "looking for someone to": 9,
    "need someone to remodel": 10,
    "want to remodel": 9,
    "planning a remodel": 9,
    "planning to renovate": 9,
    "getting quotes": 9,
    "getting estimates": 9,
    "getting bids": 9,
    "how to find a good contractor": 9,
    "best contractor": 9,
    "trusted contractor": 9,
    "reputable contractor": 9,
    "hire a contractor": 9,
    "hiring a contractor": 9,
    "looking for recommendations": 8,
    "any recommendations for": 8,
    "can anyone recommend": 8,
    "who would you recommend": 8,
    "about to start a renovation": 9,
    "starting a kitchen remodel": 10,
    "starting a bathroom remodel": 10,
    "want to redo my kitchen": 9,
    "want to redo my bathroom": 9,
    "thinking about remodeling": 8,
    "thinking about renovating": 8,
    "ready to renovate": 9,
    "budget for remodel": 8,
    "cost to remodel": 8,
    "how much does it cost to remodel": 8,
    "how much to renovate": 8,
    "remodel estimate": 8,
    # Medium-high intent (6-7): researching/considering
    "kitchen remodel": 7,
    "bathroom remodel": 7,
    "basement remodel": 7,
    "home renovation": 6,
    "house renovation": 6,
    "whole house remodel": 8,
    "gut renovation": 8,
    "high end finishes": 9,
    "luxury remodel": 9,
    "custom cabinets": 7,
    "quartz countertops": 7,
    "granite countertops": 7,
    "marble countertops": 8,
    "hardwood floors": 6,
    "tile installation": 6,
    "custom tile": 7,
    "walk in shower": 7,
    "master bathroom": 6,
    "master bath remodel": 8,
    "open concept": 6,
    "knock down a wall": 7,
    "new countertops": 7,
    "new cabinets": 7,
    "backsplash": 6,
    "crown molding": 6,
    "wainscoting": 7,
    "custom built ins": 7,
    "home addition": 7,
    "room addition": 7,
    "finished basement": 7,
    "outdoor kitchen": 7,
    "deck build": 6,
    "patio remodel": 6,
    # Competitor/referral signals (6-7)
    "bad contractor": 8,
    "contractor ghosted": 9,
    "contractor screwed": 9,
    "terrible contractor": 9,
    "worst contractor": 9,
    "contractor nightmare": 9,
    "fired my contractor": 9,
    "need to find a new contractor": 10,
    "home depot": 5,
    "lowes": 5,
    "angi": 6,
    "angie's list": 6,
    "thumbtack": 6,
    "houzz": 6,
    "homeadvisor": 6,
    # Lower intent (3-5): general discussion
    "before and after": 4,
    "remodel ideas": 5,
    "renovation ideas": 5,
    "design ideas": 4,
    "inspiration": 3,
}

# Minimum intent score to save a lead
MIN_SCORE_THRESHOLD = 4

# Database path
DB_PATH = "leads.db"

# Reddit JSON API settings
REDDIT_BASE_URL = "https://www.reddit.com"
USER_AGENT = "SocialProspector/2.0 (Lead Research Tool)"
REQUEST_DELAY = 2  # seconds between requests to be polite

# Dashboard settings
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000

# YouTube Data API v3 key (free — https://console.cloud.google.com/apis/credentials)
YOUTUBE_API_KEY = None

# YouTube search queries
YOUTUBE_SEARCH_QUERIES = [
    "kitchen remodel before and after",
    "bathroom remodel ideas",
    "how to find a good contractor",
    "home renovation tips",
    "luxury kitchen remodel",
    "high end bathroom finishes",
    "whole house renovation",
    "hiring a contractor tips",
]

# Scheduler
SCAN_INTERVAL_HOURS = 2

# Email notifications (set all to enable)
SMTP_HOST = None
SMTP_PORT = 587
SMTP_USER = None
SMTP_PASS = None
NOTIFY_EMAIL = None

# Webhook notifications (Slack/Discord)
WEBHOOK_URL = None

# White-label config
COMPANY_NAME = "Social Prospector"
COMPANY_LOGO_URL = None
BRAND_COLOR = "#daa520"

# Reddit API credentials for reply posting (via PRAW)
REDDIT_CLIENT_ID = None
REDDIT_CLIENT_SECRET = None
REDDIT_USERNAME = None
REDDIT_PASSWORD = None
