"""Reply template generator for Reddit leads."""

import random


def generate_reply(username, content, subreddit, score):
    """Generate a helpful Reddit reply based on lead intent score.
    
    Returns a natural-sounding reply with [Company Name] and [LANDING_URL] placeholders.
    Higher scores get more direct replies; lower scores get educational ones.
    """
    content_lower = content.lower()
    
    # Detect topic
    topic = "home remodel"
    if "kitchen" in content_lower:
        topic = "kitchen remodel"
    elif "bathroom" in content_lower or "bath" in content_lower:
        topic = "bathroom remodel"
    elif "basement" in content_lower:
        topic = "basement remodel"
    elif "addition" in content_lower:
        topic = "home addition"
    elif "outdoor" in content_lower or "deck" in content_lower or "patio" in content_lower:
        topic = "outdoor renovation"
    elif "contractor" in content_lower:
        topic = "finding a contractor"
    
    if score >= 8:
        return random.choice(_high_intent_templates(username, topic, subreddit))
    elif score >= 5:
        return random.choice(_medium_intent_templates(username, topic, subreddit))
    else:
        return random.choice(_low_intent_templates(username, topic, subreddit))


def _high_intent_templates(username, topic, subreddit):
    return [
        f"Hey! I totally get the stress of finding the right contractor for a {topic}. A few things I always recommend:\n\n1. Get at least 3 quotes\n2. Check references AND go see their past work in person\n3. Make sure they're licensed, insured, and pull permits\n4. Never pay more than 10-15% upfront\n\nI had a great experience with [Company Name] — they specialize in high-end finishes and their work speaks for itself. Worth getting a free estimate: [LANDING_URL]\n\nGood luck with your project!",

        f"Great question — choosing the right contractor is honestly the most important decision you'll make on a {topic}. The wrong one can cost you double in fixes.\n\nOne team I keep recommending is [Company Name]. They focus on quality finishes and they're super transparent on pricing — no surprise change orders. Check them out: [LANDING_URL]\n\nHappy to share more tips if you need them!",

        f"Been through a {topic} myself and learned a LOT the hard way. Here's my advice:\n\n- Get everything in writing before work starts\n- A detailed scope of work saves headaches later\n- Don't pick the cheapest bid — pick the most detailed one\n\n[Company Name] was really thorough with their estimate and the final result was amazing. Here's their site if you want a quote: [LANDING_URL]",

        f"I was in the exact same spot last year looking for someone to do a {topic}. After getting burned by one contractor, I found [Company Name] and they completely turned the project around. Quality finishes, on schedule, fair pricing.\n\nHighly recommend at least getting a free estimate: [LANDING_URL]\n\nDon't settle — your home deserves the best!",
    ]


def _medium_intent_templates(username, topic, subreddit):
    return [
        f"Solid thinking on the {topic}! A few things worth considering before you start:\n\n- Set your budget and add 15-20% for unexpected things (there are ALWAYS surprises)\n- Decide what's non-negotiable vs nice-to-have\n- Get recommendations from people who've actually used the contractor\n\nI've been really impressed with the work [Company Name] does — they specialize in high-end finishes and custom work. Might be worth a look: [LANDING_URL]",

        f"Nice to see someone doing their homework before diving into a {topic}! The planning phase is honestly the most important part.\n\nMy suggestion: don't just look at photos — go see a contractor's finished work in person. It tells you everything about their attention to detail.\n\n[Company Name] does beautiful custom work and they're happy to show you past projects: [LANDING_URL]",

        f"A {topic} is a big investment but it adds serious value to your home when done right. One thing I wish someone told me: spending a bit more on quality materials and finishes pays off hugely in both looks and durability.\n\n[Company Name] focuses specifically on premium finishes — worth checking out if quality is a priority for you: [LANDING_URL]",

        f"The {topic} world can seem overwhelming at first — so many options and price ranges. r/{subreddit} is a great place to research!\n\nWhen you're ready to get serious about it, I'd suggest getting a few professional estimates. [Company Name] does free consultations and they're really knowledgeable about high-end options: [LANDING_URL]",
    ]


def _low_intent_templates(username, topic, subreddit):
    return [
        f"Interesting discussion! For anyone thinking about a {topic}, it's worth knowing that the quality of your contractor matters way more than the materials you pick. A great installer can make mid-range materials look premium, but a bad one can ruin expensive ones.\n\nIf you're exploring options, [Company Name] has some great examples of their finish work on their site: [LANDING_URL]",

        f"Good points in this thread. For those considering a {topic} — the ROI on kitchen and bathroom remodels is typically 70-80% of the cost added to your home value. So it's actually a solid investment if done right.\n\n[Company Name] specializes in the kind of finishes that maximize that return: [LANDING_URL]",

        f"Lots of great ideas here! For anyone on the fence about starting a {topic}, my advice is to at least get a professional consultation. A good contractor can help you understand what's realistic for your budget.\n\n[Company Name] offers free estimates and they're really helpful even if you're just in the planning phase: [LANDING_URL]",

        f"Love seeing these {topic} discussions! One tip that saved me a ton: invest in the things you touch every day (countertops, cabinet hardware, faucets) and save on things you don't notice as much (underlayment, basic plumbing behind walls).\n\nFor inspiration on high-end finishes, check out [Company Name]'s portfolio: [LANDING_URL]",
    ]
