"""Profile: Precious Metals / Gold & Silver Dealers."""

PROFILE_NAME = "Precious Metals"
PROFILE_SLUG = "precious_metals"

SUBREDDITS = [
    "Gold", "Silverbugs", "WallStreetSilver", "investing",
    "coins", "Bullion", "PreciousMetals", "personalfinance",
    "Pmsforsale", "goldbugs", "StackSilver",
    "Numismatics", "CRH",
]

LOCAL_SUBREDDITS = []  # No geo-targeting for precious metals (nationwide)
LOCAL_REQUIRED_TERMS = []

TARGET_LOCATIONS = []  # Nationwide — no location filtering
LOCATION_SCORE_BOOST = 0

KEYWORDS = {
    # High intent (8-10): actively looking to buy
    "best place to buy gold": 10, "best place to buy silver": 10,
    "where to buy gold": 10, "where to buy silver": 10,
    "first gold purchase": 9, "first silver purchase": 9,
    "recommend a dealer": 9, "trusted dealer": 9,
    "gold dealer": 8, "silver dealer": 8, "precious metals dealer": 8,
    "looking to buy": 9, "want to start stacking": 9,
    "where can i buy": 9,
    "how to buy gold": 8, "how to buy silver": 8,
    "should i buy gold": 8, "should i buy silver": 8,
    "thinking about buying": 8,
    "just bought my first": 8, "started collecting": 7,
    "best online dealer": 9, "cheapest gold": 8, "cheapest silver": 8,
    # Medium-high intent (6-7)
    "buying gold": 7, "buying silver": 7,
    "invest in gold": 7, "invest in silver": 7,
    "gold bars": 6, "gold coins": 6, "silver bars": 6, "silver coins": 6,
    "new to gold": 7, "new to silver": 7,
    "beginner gold": 7, "beginner silver": 7,
    "stack silver": 7, "stack gold": 7,
    "gold bullion": 6, "silver bullion": 6,
    "gold bar": 6, "silver bar": 6,
    "1 oz gold": 7, "1 oz silver": 7,
    "gold ira": 8, "silver ira": 8,
    "gold etf vs physical": 7,
    # Dealer mentions (5-7)
    "apmex": 6, "jm bullion": 7, "sd bullion": 7,
    "money metals": 7, "local coin shop": 7, "lcs": 5,
    "hero bullion": 6, "bold precious metals": 6,
    "silver gold bull": 6, "monument metals": 6,
    # Lower intent (3-5)
    "gold price": 4, "silver price": 4,
    "precious metals": 3, "gold market": 3, "silver market": 3,
    "gold spot": 4, "silver spot": 4, "spot price": 4,
    "gold to silver ratio": 5, "constitutional silver": 6,
    "junk silver": 6, "90% silver": 6,
}

NEGATIVE_KEYWORDS = [
    "gold rush tv show", "gold rush season",
    "gold jewelry", "gold necklace", "gold ring", "engagement ring",
    "video game", "minecraft", "reddit gold", "gold award",
    "golden retriever", "golden state",
    "silver screen", "silver lining", "hi ho silver",
]

SELLER_SIGNALS = [
    "check out my store", "check out our store",
    "visit my shop", "visit our shop",
    "use code", "discount code", "promo code",
    "we're offering", "limited time", "sale ends",
    "free shipping on", "lowest premium",
    "dm for price", "pm for details",
]

COMPETITORS = [
    "APMEX", "JM Bullion", "SD Bullion", "Money Metals",
    "Goldco", "Birch Gold", "Augusta Precious Metals",
    "Noble Gold", "Lear Capital", "Rosland Capital",
    "Oxford Gold Group", "American Hartford Gold",
]

COMPETITOR_SUBREDDITS = [
    "Gold", "Silverbugs", "WallStreetSilver", "investing",
    "Bullion", "PreciousMetals", "Pmsforsale", "goldbugs",
]

YOUTUBE_SEARCH_QUERIES = [
    "buying gold for beginners",
    "how to buy gold", "silver stacking",
    "gold investing 2025", "best gold dealers",
    "gold vs silver investment", "gold IRA",
    "physical gold buying guide",
]

WEB_SEARCH_QUERIES = [
    '"best place to buy gold" dealer review',
    '"best place to buy silver" trusted dealer',
    '"recommend a gold dealer"',
    '"gold dealer review" buy',
    '"silver dealer" recommendation',
    '"precious metals dealer" experience',
]

CRAIGSLIST_REGIONS = []  # Not relevant for precious metals

FB_GROUPS = [
    "https://www.facebook.com/groups/goldandsilverinvesting",
    "https://www.facebook.com/groups/silverstacking",
    "https://www.facebook.com/groups/preciousmetalsinvesting",
    "https://www.facebook.com/groups/goldbullion",
    "https://www.facebook.com/groups/silverbullion",
]

REPLY_TEMPLATES = {
    "high": "Great question! When buying {topic}, the key is finding a dealer with transparent pricing (low premiums over spot) and solid reputation. I'd recommend comparing at least 3-4 dealers before pulling the trigger. Happy to share some resources on what to look for if you're interested.",
    "medium": "If you're getting into {topic}, one tip is to always check the premium over spot price — that's where dealers make their money. Some charge way more than others for the same product. Let me know if you want some pointers.",
    "low": "Welcome to the stack! {topic} is a solid move. Feel free to ask if you have questions about getting started.",
}
