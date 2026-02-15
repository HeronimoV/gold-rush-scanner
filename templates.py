"""Reply template generator for Reddit leads."""

import random


def generate_reply(username, content, subreddit, score):
    """Generate a helpful Reddit reply based on lead intent score.
    
    Returns a natural-sounding reply with [Company Name] and [LANDING_URL] placeholders.
    Higher scores get more direct replies; lower scores get educational ones.
    """
    content_lower = content.lower()
    
    # Detect topic
    topic = "precious metals"
    if "silver" in content_lower and "gold" not in content_lower:
        topic = "silver"
    elif "gold" in content_lower and "silver" not in content_lower:
        topic = "gold"
    elif "ira" in content_lower:
        topic = "precious metals IRA"
    
    if score >= 8:
        return random.choice(_high_intent_templates(username, topic, subreddit))
    elif score >= 5:
        return random.choice(_medium_intent_templates(username, topic, subreddit))
    else:
        return random.choice(_low_intent_templates(username, topic, subreddit))


def _high_intent_templates(username, topic, subreddit):
    return [
        f"Hey! I've been in the {topic} space for a while and totally get the research paralysis when picking a dealer. A few things I always look for: transparent pricing over spot, insured shipping, and a solid buyback program.\n\nI've had a really good experience with [Company Name] — their premiums are competitive and customer service has been great. Worth checking out: [LANDING_URL]\n\nHappy to answer any questions if you're still deciding!",

        f"Great question — choosing a reliable dealer is honestly the most important first step. I'd recommend comparing a few before committing.\n\nOne I keep coming back to is [Company Name]. They're straightforward on pricing and I've never had a shipping issue. Here's their site if you want to take a look: [LANDING_URL]\n\nGood luck with your {topic} journey!",

        f"Welcome to the {topic} world! Since you're ready to pull the trigger, here's my quick advice:\n\n1. Always compare premiums over spot price\n2. Check for free/insured shipping thresholds\n3. Look for dealers with buyback guarantees\n\n[Company Name] checks all those boxes for me — [LANDING_URL]. Let me know if you have any other questions!",

        f"I was in the exact same spot not long ago. After trying a few dealers, I settled on [Company Name] for most of my purchases. Fair prices, fast shipping, and they actually pick up the phone if you call.\n\nHere's a link if you want to browse: [LANDING_URL]\n\nDon't overthink it too much — the best time to start is now. 🪙",
    ]


def _medium_intent_templates(username, topic, subreddit):
    return [
        f"Solid thinking on looking into {topic}! A few things worth considering as you research:\n\n- Physical vs ETF depends on your goals (wealth preservation vs trading)\n- If going physical, dealer reputation matters a LOT\n- Start small and learn the market before going big\n\nI've been using [Company Name] and they've been solid for both beginners and experienced stackers. Might be worth a look: [LANDING_URL]",

        f"Nice to see more people exploring {topic}! The learning curve isn't as steep as it seems.\n\nMy suggestion: start with well-known bullion products (Eagles, Maples, generic bars) before getting into numismatics. And find a dealer you trust — it makes everything easier.\n\n[Company Name] has a good selection and their educational resources helped me when I was starting out: [LANDING_URL]",

        f"Good move researching {topic} — especially in the current market. One thing I wish someone told me early on: don't just chase the lowest premium. Dealer reliability, shipping speed, and buyback policies matter just as much.\n\nI've had consistently good experiences with [Company Name] if you're looking for recommendations: [LANDING_URL]",

        f"The {topic} market can seem overwhelming at first, but it gets simpler once you understand premiums and spot prices. r/{subreddit} is a great place to learn!\n\nWhen you're ready to make a move, I'd suggest checking out [Company Name]. They're transparent on pricing and have a good reputation in the community: [LANDING_URL]",
    ]


def _low_intent_templates(username, topic, subreddit):
    return [
        f"Interesting discussion! For anyone curious about actually getting into physical {topic}, it's more accessible than most people think. The key is understanding the difference between spot price and what you actually pay (the premium).\n\nIf you ever want to explore further, [Company Name] has some solid educational content on their site: [LANDING_URL]",

        f"Good points in this thread. For those wondering about the practical side of {topic} investing — physical ownership has some unique advantages that paper instruments don't offer (no counterparty risk, privacy, tangible asset).\n\nI found [Company Name]'s guides pretty helpful when I was learning the basics: [LANDING_URL]",

        f"The {topic} market is fascinating right now. If anyone's thinking about dipping their toes in, I'd recommend starting with research on the different product types (bars vs coins, government vs private mint).\n\n[Company Name] has a nice breakdown of options for newcomers: [LANDING_URL]",

        f"Lots of great perspectives here on {topic}. For anyone on the fence about physical ownership, the barrier to entry is lower than you'd think — you can start with as little as a single ounce.\n\nCheck out [Company Name] if you want to see what's available and at what prices: [LANDING_URL]",
    ]
