"""Profile: Home Remodeling — Colorado geo-targeted."""

PROFILE_NAME = "Home Remodeling (Colorado)"
PROFILE_SLUG = "remodeling_colorado"

SUBREDDITS = [
    # Colorado local subreddits
    "Denver", "Colorado", "ColoradoSprings", "FortCollins",
    "Boulder", "AuroraCO", "Pueblo", "GrandJunction", "Longmont",
    # National remodeling subreddits
    "HomeImprovement", "InteriorDesign", "kitchenremodel", "DIY",
    "homeowners", "RealEstate", "firsttimehomebuyer", "centuryhomes", "Renovations",
]

LOCAL_SUBREDDITS = [
    "Denver", "Colorado", "ColoradoSprings", "FortCollins",
    "Boulder", "AuroraCO", "Pueblo", "GrandJunction", "Longmont",
]

LOCAL_REQUIRED_TERMS = [
    "remodel", "renovate", "renovation", "contractor", "remodeler",
    "kitchen remodel", "bathroom remodel", "basement remodel",
    "flooring", "countertop", "cabinet", "backsplash", "hardwood floor",
    "drywall", "plumbing", "electrical work", "home addition", "deck build",
    "patio", "molding", "built-in", "handyman",
    "home improvement", "home repair", "fixer upper", "fixer-upper",
    "general contractor", "remodeling", "tile install", "tile work",
    "new kitchen", "new bathroom", "gut reno", "demo day",
    "knock down wall", "open concept", "new countertop", "new cabinet",
    "roof repair", "roof replace", "siding", "window replace",
    "hvac", "furnace", "water heater", "garage conversion",
]

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
]
LOCATION_SCORE_BOOST = 3

KEYWORDS = {
    "looking for a contractor": 10, "need a contractor": 10,
    "recommend a contractor": 10, "looking for a remodeler": 10,
    "need a remodeler": 10, "recommend a remodeler": 10,
    "who did your remodel": 9,
    "looking for someone to remodel": 9, "looking for someone to renovate": 9,
    "looking for someone to build": 8, "looking for someone to install": 8,
    "need someone to remodel": 10,
    "want to remodel": 9, "planning a remodel": 9, "planning to renovate": 9,
    "getting quotes": 9, "getting estimates": 9, "getting bids": 9,
    "how to find a good contractor": 9, "best contractor": 9,
    "trusted contractor": 9, "reputable contractor": 9,
    "hire a contractor": 9, "hiring a contractor": 9,
    "looking for contractor recommendations": 8, "looking for remodeler recommendations": 8,
    "any recommendations for contractor": 8, "any recommendations for remodel": 8,
    "can anyone recommend a contractor": 8, "can anyone recommend a remodeler": 8,
    "who would you recommend for": 7,
    "about to start a renovation": 9,
    "starting a kitchen remodel": 10, "starting a bathroom remodel": 10,
    "want to redo my kitchen": 9, "want to redo my bathroom": 9,
    "thinking about remodeling": 8, "thinking about renovating": 8,
    "ready to renovate": 9,
    "budget for remodel": 8, "cost to remodel": 8,
    "how much does it cost to remodel": 8, "how much to renovate": 8,
    "remodel estimate": 8,
    "kitchen remodel": 7, "bathroom remodel": 7, "basement remodel": 7,
    "home renovation": 6, "house renovation": 6,
    "whole house remodel": 8, "gut renovation": 8,
    "high end finishes": 9, "luxury remodel": 9,
    "custom cabinets": 7, "quartz countertops": 7,
    "granite countertops": 7, "marble countertops": 8,
    "hardwood floors": 6, "tile installation": 6, "custom tile": 7,
    "walk in shower": 7, "master bathroom": 6, "master bath remodel": 8,
    "open concept": 6, "knock down a wall": 7,
    "new countertops": 7, "new cabinets": 7,
    "backsplash": 6, "crown molding": 6, "wainscoting": 7,
    "custom built ins": 7, "home addition": 7, "room addition": 7,
    "finished basement": 7, "outdoor kitchen": 7,
    "deck build": 6, "patio remodel": 6,
    "bad contractor": 8, "contractor ghosted": 9, "contractor screwed": 9,
    "terrible contractor": 9, "worst contractor": 9,
    "contractor nightmare": 9, "fired my contractor": 9,
    "need to find a new contractor": 10,
    "home depot": 5, "lowes": 5, "angi": 6, "angie's list": 6,
    "thumbtack": 6, "houzz": 6, "homeadvisor": 6,
    "before and after": 4, "remodel ideas": 5,
    "renovation ideas": 5, "design ideas": 4, "inspiration": 3,
}

NEGATIVE_KEYWORDS = [
    "things to do this weekend", "things to do in",
    "events this week", "weekend events",
    "hair salon", "hair stylist", "haircut",
    "restaurant", "brunch", "happy hour",
    "hiking trail", "camping", "ski",
    "roommate", "sublease", "take over my lease", "relet",
    "lost dog", "lost cat", "missing pet",
    "job posting", "hiring for", "we're hiring",
    "moving to", "moving from",
    "jellyfish", "aquarium", "fish tank",
    "welcome to this gorgeous home", "just listed", "just sold",
    "open house", "under contract", "for rent", "for lease",
]

SELLER_SIGNALS = [
    "i build", "we build", "i handcraft", "we handcraft",
    "i make", "we make", "locally built", "handmade",
    "check out my", "check out our", "visit my", "visit our",
    "free estimate", "free consultation", "call us", "call me",
    "our services", "my services", "we offer", "i offer",
    "years of experience", "licensed and insured",
    "serving the denver", "serving colorado",
    "dm for price", "order now", "book now",
]

COMPETITORS = [
    "Home Depot", "Lowe's", "Angi", "Angie's List",
    "HomeAdvisor", "Thumbtack", "Houzz", "Porch",
    "Mr. Handyman", "Bath Fitter", "Re-Bath",
]

COMPETITOR_SUBREDDITS = [
    "Denver", "Colorado", "ColoradoSprings", "FortCollins", "Boulder",
    "HomeImprovement", "homeowners", "Renovations",
]

YOUTUBE_SEARCH_QUERIES = [
    "kitchen remodel before and after",
    "bathroom remodel ideas",
    "how to find a good contractor",
    "home renovation tips",
    "luxury kitchen remodel",
    "whole house renovation",
]

WEB_SEARCH_QUERIES = [
    '"looking for a contractor" Denver remodel',
    '"need a remodeler" Colorado',
    '"kitchen remodel" Denver contractor',
    '"bathroom remodel" Colorado Springs',
    '"contractor recommendations" Boulder remodel',
    '"Fort Collins" remodel contractor',
]

CRAIGSLIST_REGIONS = ["denver", "cosprings", "boulder", "fortcollins", "pueblo", "westslope", "highrockies"]

FB_GROUPS = [
    "https://www.facebook.com/groups/denverHomeImprovement",
    "https://www.facebook.com/groups/DenverContractors",
    "https://www.facebook.com/groups/ColoradoHomeImprovement",
    "https://www.facebook.com/groups/DenverRealEstate",
    "https://www.facebook.com/groups/coloradospringsrealestate",
    "https://www.facebook.com/groups/FortCollinsHomeImprovement",
    "https://www.facebook.com/groups/BoulderHomeImprovement",
]

REPLY_TEMPLATES = {
    "high": "Great question! For {topic} in Colorado, it's worth getting 3+ quotes from local contractors. A good remodeler will do a free walk-through and give you a detailed estimate. Happy to point you toward some resources if you'd like — we track contractor quality across the Front Range.",
    "medium": "If you're looking into {topic}, one thing that helps is checking reviews on multiple platforms (not just one). The quality of contractors varies a lot. If you want, I can share some tips on what to look for.",
    "low": "Good topic! {topic} can really add value to your home. Let me know if you have specific questions about the process.",
}
