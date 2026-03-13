"""Generate personalized outreach messages for leads."""

def generate_dm(lead_data):
    """Generate a personalized DM for a lead.
    
    Args:
        lead_data: dict with keys: username, content, intent_score, subreddit
    
    Returns:
        str: Personalized DM message
    """
    username = lead_data.get('username', '')
    content = lead_data.get('content', '').lower()
    score = lead_data.get('intent_score', 0)
    subreddit = lead_data.get('subreddit', '')
    
    # Detect buyer signals
    is_first_time = any(x in content for x in ['first', 'new to', 'beginner', 'just started'])
    is_wtb = '[wtb]' in content or 'want to buy' in content or 'looking to buy' in content
    mentions_dealer = any(x in content for x in ['apmex', 'jm bullion', 'sd bullion', 'monument metals'])
    asking_question = '?' in content
    
    # Generate personalized message
    if is_first_time:
        template = f"""Hey {username}! 👋

Saw your post on r/{subreddit} — congrats on starting your precious metals journey! 🎉

As someone who's been stacking for a while, here are a few quick tips that helped me:

1. **Compare premiums** — Some dealers charge 10-15% over spot, others charge 3-5%. Always shop around.
2. **Start with 1oz rounds/bars** — Easiest to sell later, most liquid
3. **Local coin shops (LCS)** — No shipping delays, build relationships, sometimes better deals on bulk

If you're looking for trusted online dealers, the big 3 are:
- **JM Bullion** (best selection)
- **SD Bullion** (lowest premiums usually)
- **APMEX** (premium quality, slightly higher prices)

Also check r/Pmsforsale for peer-to-peer deals (verify seller feedback first!).

Happy to answer any questions — feel free to DM. Welcome to the stack! 🪙"""

    elif is_wtb:
        template = f"""Hey {username}! 👋

Saw your WTB post on r/{subreddit}. I've had great luck finding deals by:

1. **Checking dealer inventory daily** — JM Bullion, SD Bullion, Monument Metals all have "deals" sections
2. **r/Pmsforsale** — Peer-to-peer often beats dealer prices (just verify seller feedback)
3. **Local coin shops** — Call around, some have wild deals on generic rounds

What are you looking for specifically? I might know where to find it.

Happy hunting! 🪙"""

    elif asking_question:
        template = f"""Hey {username}! 👋

Saw your question on r/{subreddit} and wanted to share what's worked for me.

**Quick answer:** The best dealer depends on what you're buying. For generics (rounds/bars), I go lowest premium — usually SD Bullion or Monument Metals. For numismatics or specific coins, APMEX has the best selection.

**Pro tip:** Sign up for email alerts from 3-4 dealers. They run flash sales (15-30 min) with crazy low premiums. That's where the real deals are.

Also, if you're buying $1K+, call dealers directly and ask for bulk pricing. Most will beat their website price by 2-5%.

Hope that helps! Happy to answer any other questions. 🪙"""

    elif score >= 6:
        template = f"""Hey {username}! 👋

Saw your post on r/{subreddit}. If you're shopping for gold/silver, here's a quick tip most people don't know:

**Dealer premiums vary WILDLY.** The same 1oz silver bar can be $32 at one site and $35 at another. I use a comparison tool to check 5-6 dealers at once before I buy.

The "big 3" I check every time:
- JM Bullion
- SD Bullion
- Monument Metals

Also: sign up for their email lists. They do flash sales with insane low premiums (like spot +$1 on silver).

Happy stacking! 🪙"""

    else:
        # Low intent — just a soft touch
        template = f"""Hey {username}! 👋

Saw your comment on r/{subreddit}. If you're ever looking to pick up some gold/silver, happy to share what's worked for me. Took me years to figure out which dealers are legit vs which ones overcharge like crazy.

Feel free to reach out anytime! 🪙"""

    return template


def generate_comment_reply(lead_data):
    """Generate a helpful public comment reply (not a DM).
    
    More subtle, provides value, no hard sell.
    """
    content = lead_data.get('content', '').lower()
    score = lead_data.get('intent_score', 0)
    
    is_first_time = any(x in content for x in ['first', 'new to', 'beginner', 'just started'])
    asking_dealer = any(x in content for x in ['where to buy', 'best place', 'recommend a dealer', 'trusted dealer'])
    
    if is_first_time:
        return """Welcome to the stack! A few tips that helped me when I started:

1. **Compare premiums** (price over spot) across 3-4 dealers before buying
2. **Start with generic 1oz rounds** — easiest to sell later, most liquid
3. **Check r/Pmsforsale** for peer-to-peer deals (verify seller feedback!)

The big dealers I use: JM Bullion (best selection), SD Bullion (lowest premiums), Monument Metals (fast shipping). All have solid reputations.

Happy stacking! 🪙"""

    elif asking_dealer:
        return """The "big 3" that most stackers trust:

- **JM Bullion** — huge selection, fast shipping
- **SD Bullion** — usually lowest premiums
- **APMEX** — premium quality, slightly higher prices

Pro tip: Sign up for email alerts. They all do flash sales (15-30 min windows) with spot +$1-2 on silver. That's where the real deals are.

Also check r/Pmsforsale for peer-to-peer — often beats dealer prices (just verify seller feedback first).

Happy hunting! 🪙"""

    elif score >= 6:
        return """Pro tip: dealer premiums vary wildly. Same 1oz bar can be $32 at one site, $35 at another. 

I check JM Bullion, SD Bullion, and Monument Metals every time before buying. Sign up for their email lists — flash sales are where the deals are (spot +$1-2 on silver).

Happy stacking! 🪙"""

    else:
        return """If you're buying, always compare premiums across 3-4 dealers. I use JM Bullion, SD Bullion, Monument Metals. Sign up for email alerts — flash sales have the best prices.

Happy stacking! 🪙"""
