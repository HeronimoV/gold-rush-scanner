#!/usr/bin/env python3
"""Clean the database — remove all non-Reddit leads (dealer websites, etc.)

For precious_metals profile, we ONLY want Reddit users (real people).
Web scanner finds dealer websites — completely useless.
"""

import sqlite3

def clean_database():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    
    # Count before
    c.execute("SELECT COUNT(*) FROM leads")
    total_before = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM leads WHERE platform != 'reddit'")
    non_reddit = c.fetchone()[0]
    
    print(f"📊 Database stats:")
    print(f"   Total leads: {total_before}")
    print(f"   Non-Reddit (web/YouTube/etc.): {non_reddit}")
    print(f"   Reddit leads: {total_before - non_reddit}")
    
    if non_reddit > 0:
        print(f"\n🗑️  Deleting {non_reddit} non-Reddit leads (dealer websites, etc.)...")
        c.execute("DELETE FROM leads WHERE platform != 'reddit'")
        conn.commit()
        print("   ✅ Deleted!")
    
    # Also remove any Reddit leads that look like dealers (username is a website)
    c.execute('''
        DELETE FROM leads 
        WHERE platform = 'reddit' 
        AND (
            username LIKE '%.com' 
            OR username LIKE '%.net' 
            OR username LIKE '%.org'
            OR username LIKE '%dealer%'
            OR username LIKE '%bullion%'
        )
    ''')
    deleted_suspicious = c.rowcount
    if deleted_suspicious > 0:
        print(f"🗑️  Deleted {deleted_suspicious} suspicious Reddit usernames (look like websites)")
    
    conn.commit()
    
    # Count after
    c.execute("SELECT COUNT(*) FROM leads WHERE platform = 'reddit'")
    total_after = c.fetchone()[0]
    
    print(f"\n✅ Database cleaned!")
    print(f"   {total_after} real Reddit leads remaining")
    print(f"   {total_before - total_after} total deleted")
    
    conn.close()

if __name__ == "__main__":
    print("🧹 Cleaning leads database...\n")
    clean_database()
