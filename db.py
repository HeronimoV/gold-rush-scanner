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

    # Reply queue table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reply_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            reply_text TEXT NOT NULL,
            target_url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            posted_at TEXT,
            error_message TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rq_status ON reply_queue(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rq_lead ON reply_queue(lead_id)")

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


def add_to_queue(lead_id, reply_text, target_url):
    """Add a reply to the queue. Returns the new queue item id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO reply_queue (lead_id, reply_text, target_url, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (lead_id, reply_text, target_url, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_queue_items(status=None, limit=100):
    """Fetch queue items, optionally filtered by status."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT rq.*, l.username, l.content as lead_content, l.subreddit, l.intent_score "
            "FROM reply_queue rq LEFT JOIN leads l ON rq.lead_id = l.id "
            "WHERE rq.status = ? ORDER BY rq.created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT rq.*, l.username, l.content as lead_content, l.subreddit, l.intent_score "
            "FROM reply_queue rq LEFT JOIN leads l ON rq.lead_id = l.id "
            "ORDER BY CASE rq.status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 WHEN 'failed' THEN 2 WHEN 'posted' THEN 3 ELSE 4 END, rq.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_queue_status(queue_id, status, error=None):
    """Update a queue item's status."""
    conn = get_connection()
    if error is not None:
        conn.execute("UPDATE reply_queue SET status = ?, error_message = ? WHERE id = ?", (status, error, queue_id))
    else:
        conn.execute("UPDATE reply_queue SET status = ? WHERE id = ?", (status, queue_id))
    conn.commit()
    conn.close()


def get_queue_stats():
    """Get reply queue statistics."""
    conn = get_connection()
    pending = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE status = 'pending'").fetchone()["c"]
    approved = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE status = 'approved'").fetchone()["c"]
    total_posted = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE status = 'posted'").fetchone()["c"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posted_today = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE status = 'posted' AND posted_at >= ?", (today,)).fetchone()["c"]
    failed = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE status = 'failed'").fetchone()["c"]
    conn.close()
    return {
        "pending": pending,
        "approved": approved,
        "total_posted": total_posted,
        "posted_today": posted_today,
        "failed": failed,
    }


def is_lead_queued(lead_id):
    """Check if a lead already has a queue entry."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as c FROM reply_queue WHERE lead_id = ?", (lead_id,)).fetchone()
    conn.close()
    return row["c"] > 0


# Auto-init on import
init_db()
