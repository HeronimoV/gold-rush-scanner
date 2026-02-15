"""Weekly report generator for Gold Rush Scanner."""

import sqlite3
from datetime import datetime, timezone, timedelta
from config import DB_PATH


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def generate_weekly_report():
    """Generate a weekly summary report. Returns dict with 'html' and 'text' keys."""
    conn = _get_conn()
    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    # Total new leads this week
    total = conn.execute("SELECT COUNT(*) as c FROM leads WHERE found_at >= ?", (week_ago,)).fetchone()["c"]

    # By subreddit
    by_sub = conn.execute(
        "SELECT subreddit, COUNT(*) as c FROM leads WHERE found_at >= ? GROUP BY subreddit ORDER BY c DESC",
        (week_ago,),
    ).fetchall()

    # By score tier
    high = conn.execute("SELECT COUNT(*) as c FROM leads WHERE found_at >= ? AND intent_score >= 8", (week_ago,)).fetchone()["c"]
    medium = conn.execute("SELECT COUNT(*) as c FROM leads WHERE found_at >= ? AND intent_score >= 5 AND intent_score < 8", (week_ago,)).fetchone()["c"]
    low = conn.execute("SELECT COUNT(*) as c FROM leads WHERE found_at >= ? AND intent_score < 5", (week_ago,)).fetchone()["c"]

    # Top 10 highest-intent leads
    top_leads = conn.execute(
        "SELECT username, subreddit, intent_score, content, url, found_at FROM leads WHERE found_at >= ? ORDER BY intent_score DESC, found_at DESC LIMIT 10",
        (week_ago,),
    ).fetchall()

    # Form submissions this week
    form_count = conn.execute("SELECT COUNT(*) as c FROM form_leads WHERE submitted_at >= ?", (week_ago,)).fetchone()["c"]

    conn.close()

    # Build plain text
    lines = [
        f"Gold Rush Scanner — Weekly Report",
        f"Period: {(now - timedelta(days=7)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        f"{'=' * 50}",
        f"",
        f"Total new leads: {total}",
        f"Form submissions: {form_count}",
        f"",
        f"Score tiers:",
        f"  🔥 High (8-10): {high}",
        f"  🟡 Medium (5-7): {medium}",
        f"  ⚪ Low (1-4): {low}",
        f"",
        f"By subreddit:",
    ]
    for r in by_sub:
        lines.append(f"  r/{r['subreddit']}: {r['c']}")
    lines += ["", "Top 10 highest-intent leads:"]
    for i, l in enumerate(top_leads, 1):
        lines.append(f"  {i}. u/{l['username']} (score {l['intent_score']}) in r/{l['subreddit']} — {l['url']}")

    text = "\n".join(lines)

    # Build HTML
    sub_rows = "".join(f"<tr><td style='padding:6px 12px'>r/{r['subreddit']}</td><td style='padding:6px 12px;text-align:right'>{r['c']}</td></tr>" for r in by_sub)
    lead_rows = ""
    for l in top_leads:
        lead_rows += f"""<tr>
            <td style='padding:6px 8px'><strong>{l['intent_score']}</strong></td>
            <td style='padding:6px 8px'><a href='https://reddit.com/u/{l['username']}'>u/{l['username']}</a></td>
            <td style='padding:6px 8px'>r/{l['subreddit']}</td>
            <td style='padding:6px 8px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'>{l['content'][:120]}</td>
            <td style='padding:6px 8px'><a href='{l['url']}'>link</a></td>
        </tr>"""

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:800px;margin:0 auto;background:#0f1117;color:#e0e0e0;padding:24px;border-radius:8px">
      <h1 style="color:#daa520">⛏️ Gold Rush Scanner — Weekly Report</h1>
      <p style="color:#999">{(now - timedelta(days=7)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}</p>

      <div style="display:flex;gap:16px;flex-wrap:wrap;margin:20px 0">
        <div style="background:#1a1d27;padding:16px 20px;border-radius:8px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#daa520">{total}</div><div style="color:#999;font-size:13px">New Leads</div>
        </div>
        <div style="background:#1a1d27;padding:16px 20px;border-radius:8px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#2a5">{high}</div><div style="color:#999;font-size:13px">High Intent</div>
        </div>
        <div style="background:#1a1d27;padding:16px 20px;border-radius:8px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#b8860b">{medium}</div><div style="color:#999;font-size:13px">Medium</div>
        </div>
        <div style="background:#1a1d27;padding:16px 20px;border-radius:8px;flex:1;min-width:120px;text-align:center">
          <div style="font-size:28px;font-weight:700;color:#daa520">{form_count}</div><div style="color:#999;font-size:13px">Form Leads</div>
        </div>
      </div>

      <h3 style="color:#daa520;margin-top:24px">By Subreddit</h3>
      <table style="width:100%;border-collapse:collapse;margin:8px 0">
        <tr style="border-bottom:2px solid #b8860b"><th style="padding:8px 12px;text-align:left">Subreddit</th><th style="padding:8px 12px;text-align:right">Leads</th></tr>
        {sub_rows}
      </table>

      <h3 style="color:#daa520;margin-top:24px">Top 10 Highest-Intent Leads</h3>
      <table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:13px">
        <tr style="border-bottom:2px solid #b8860b"><th style="padding:6px 8px">Score</th><th style="padding:6px 8px">User</th><th style="padding:6px 8px">Subreddit</th><th style="padding:6px 8px">Content</th><th style="padding:6px 8px">Link</th></tr>
        {lead_rows}
      </table>

      <p style="margin-top:24px;color:#555;font-size:12px">Generated by Gold Rush Scanner</p>
    </div>
    """

    return {"html": html, "text": text, "stats": {"total": total, "high": high, "medium": medium, "low": low, "form_count": form_count}}
