"""SQLite database layer for leads storage and deduplication."""

import sqlite3
from datetime import datetime, timezone, timedelta
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL DEFAULT 'reddit',
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            subreddit TEXT NOT NULL,
            intent_score INTEGER NOT NULL,
            found_at TEXT NOT NULL,
            contacted INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON leads(username)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON leads(intent_score)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_subreddit ON leads(subreddit)")

    # Form leads table for landing page submissions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS form_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            interest TEXT NOT NULL DEFAULT '',
            budget TEXT NOT NULL DEFAULT '',
            referral_source TEXT NOT NULL DEFAULT '',
            submitted_at TEXT NOT NULL,
            contacted INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        )
    """)

    # Add notes column to existing leads table if missing
    try:
        conn.execute("ALTER TABLE leads ADD COLUMN notes TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()


def insert_lead(platform, username, content, url, subreddit, intent_score, found_at=None):
    """Insert a lead, skipping if URL already exists. Returns True if inserted."""
    if found_at is None:
        found_at = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO leads (platform, username, content, url, subreddit, intent_score, found_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (platform, username, content[:2000], url, subreddit, intent_score, found_at),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def insert_form_lead(name, email, phone, interest, budget, referral_source):
    """Insert a form submission lead."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO form_leads (name, email, phone, interest, budget, referral_source, submitted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, email, phone, interest, budget, referral_source, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_form_leads(limit=500):
    """Fetch form leads."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM form_leads ORDER BY submitted_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_notes(lead_id, notes):
    """Update notes for a lead."""
    conn = get_connection()
    conn.execute("UPDATE leads SET notes = ? WHERE id = ?", (notes, lead_id))
    conn.commit()
    conn.close()


def update_form_lead_notes(lead_id, notes):
    """Update notes for a form lead."""
    conn = get_connection()
    conn.execute("UPDATE form_leads SET notes = ? WHERE id = ?", (notes, lead_id))
    conn.commit()
    conn.close()


def mark_form_lead_contacted(lead_id):
    """Toggle contacted status for a form lead."""
    conn = get_connection()
    conn.execute(
        "UPDATE form_leads SET contacted = CASE WHEN contacted = 0 THEN 1 ELSE 0 END WHERE id = ?",
        (lead_id,),
    )
    conn.commit()
    conn.close()


def get_leads(min_score=None, subreddit=None, date_from=None, contacted=None, limit=500):
    """Fetch leads with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if min_score is not None:
        query += " AND intent_score >= ?"
        params.append(min_score)
    if subreddit:
        query += " AND subreddit = ?"
        params.append(subreddit)
    if date_from:
        query += " AND found_at >= ?"
        params.append(date_from)
    if contacted is not None:
        query += " AND contacted = ?"
        params.append(int(contacted))

    query += " ORDER BY intent_score DESC, found_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_contacted(lead_id):
    """Toggle contacted status for a lead."""
    conn = get_connection()
    conn.execute(
        "UPDATE leads SET contacted = CASE WHEN contacted = 0 THEN 1 ELSE 0 END WHERE id = ?",
        (lead_id,),
    )
    conn.commit()
    conn.close()


def get_subreddits():
    """Get list of distinct subreddits in the database."""
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT subreddit FROM leads ORDER BY subreddit").fetchall()
    conn.close()
    return [r["subreddit"] for r in rows]


def get_stats():
    """Get summary statistics."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()["c"]
    high = conn.execute("SELECT COUNT(*) as c FROM leads WHERE intent_score >= 7").fetchone()["c"]
    contacted = conn.execute("SELECT COUNT(*) as c FROM leads WHERE contacted = 1").fetchone()["c"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_count = conn.execute("SELECT COUNT(*) as c FROM leads WHERE found_at >= ?", (today,)).fetchone()["c"]

    avg_row = conn.execute("SELECT AVG(intent_score) as a FROM leads").fetchone()
    avg_score = round(avg_row["a"], 1) if avg_row["a"] else 0

    top_sub_row = conn.execute(
        "SELECT subreddit, COUNT(*) as c FROM leads GROUP BY subreddit ORDER BY c DESC LIMIT 1"
    ).fetchone()
    top_subreddit = top_sub_row["subreddit"] if top_sub_row else "—"

    form_count = conn.execute("SELECT COUNT(*) as c FROM form_leads").fetchone()["c"]

    conn.close()
    return {
        "total": total,
        "high_intent": high,
        "contacted": contacted,
        "today": today_count,
        "avg_score": avg_score,
        "top_subreddit": top_subreddit,
        "form_leads": form_count,
    }


# Auto-init on import
init_db()
