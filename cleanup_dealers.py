#!/usr/bin/env python3
"""Clean dealer/commercial websites from leads database.

These are useless — we want real buyers, not dealer websites.
"""

import sqlite3

# Known dealer/commercial domains to remove
DEALER_DOMAINS = [
    'apmex.com',
    'jmbullion.com',
    'sdbullion.com',
    'monumentmetals.com',
    'herobullion.com',
    'silvergoldbull.com',
    'boldpreciousmetals.com',
    'gainesvillecoins.com',
    'investopedia.com',
    'nerdwallet.com',
    'businessinsider.com',
    'golddealerreviews.com',
    'mitrade.com',
    'goldirablueprint.com',
    'pacificpreciousmetals.com',
    'moneymetals.com',
    'birchgold.com',
    'augustapreciousmetals.com',
    'goldco.com',
    'noblegoldinvestments.com',
    'learcapital.com',
    'roslandcapital.com',
    'oxfordgoldgroup.com',
    'americanhartfordgold.com',
    # Add generic patterns
    'dealer',
    'bullion.com',
    'golddealer',
    'silverdealer',
    'preciousmetals.com',
    'goldinvestment',
    'silverinvestment',
]

def clean_dealer_leads(dry_run=True):
    """Remove dealer website leads from database.
    
    Args:
        dry_run: If True, only show what would be deleted
    """
    conn = sqlite3.connect('leads.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Find all leads with dealer domains in URL or username
    deleted_count = 0
    for domain in DEALER_DOMAINS:
        c.execute('''
            SELECT id, username, url, platform 
            FROM leads 
            WHERE platform != 'reddit' 
               OR url LIKE ? 
               OR username LIKE ?
        ''', (f'%{domain}%', f'%{domain}%'))
        
        matches = c.fetchall()
        if matches:
            print(f"\n🗑️  Domain: {domain} — {len(matches)} leads")
            for row in matches[:3]:  # Show first 3 examples
                print(f"   - {row['username']} | {row['url']}")
            
            if not dry_run:
                ids = [row['id'] for row in matches]
                c.execute(f"DELETE FROM leads WHERE id IN ({','.join('?' * len(ids))})", ids)
                deleted_count += len(ids)
    
    # Also remove any non-reddit platform leads (web scraper results)
    c.execute("SELECT COUNT(*) FROM leads WHERE platform != 'reddit'")
    non_reddit_count = c.fetchone()[0]
    
    if non_reddit_count > 0:
        print(f"\n🗑️  Non-Reddit leads: {non_reddit_count}")
        if not dry_run:
            c.execute("DELETE FROM leads WHERE platform != 'reddit'")
            deleted_count += non_reddit_count
    
    if dry_run:
        print(f"\n📊 DRY RUN: Would delete ~{deleted_count} dealer/web leads")
        print("   Run with --execute to actually delete")
    else:
        conn.commit()
        print(f"\n✅ Deleted {deleted_count} dealer/web leads")
    
    # Show remaining stats
    c.execute("SELECT COUNT(*) FROM leads WHERE platform = 'reddit'")
    reddit_count = c.fetchone()[0]
    print(f"✅ {reddit_count} real Reddit leads remaining")
    
    conn.close()

if __name__ == "__main__":
    import sys
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("🔍 DRY RUN MODE — No changes will be made")
        print("   Run with --execute to actually delete\n")
    
    clean_dealer_leads(dry_run=dry_run)
