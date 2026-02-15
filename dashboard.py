#!/usr/bin/env python3
"""Flask dashboard for viewing and managing leads."""

import csv
import io
import os
import threading
import time as _time
from flask import Flask, render_template_string, request, redirect, url_for, Response, jsonify, send_from_directory

from config import DASHBOARD_HOST, DASHBOARD_PORT
from db import (
    get_leads, mark_contacted, get_subreddits, get_stats,
    update_notes, insert_form_lead, get_form_leads,
    update_form_lead_notes, mark_form_lead_contacted,
)
from templates import generate_reply
from reports import generate_weekly_report

app = Flask(__name__)

# --- Background scanner ---
_scan_status = {"running": False, "last_run": None, "last_count": 0}

def _run_scan_bg():
    """Run scanner in background thread."""
    from scanner import run_full_scan
    _scan_status["running"] = True
    try:
        count = run_full_scan()
        _scan_status["last_count"] = count
        from datetime import datetime, timezone
        _scan_status["last_run"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    finally:
        _scan_status["running"] = False

def _auto_scan_loop():
    """Auto-scan every 2 hours."""
    while True:
        _time.sleep(10)  # initial delay
        if not _scan_status["running"]:
            _run_scan_bg()
        _time.sleep(7190)  # ~2 hours

# Start auto-scan thread
_auto_thread = threading.Thread(target=_auto_scan_loop, daemon=True)
_auto_thread.start()

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gold Rush Scanner — Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; }
  .header { background: linear-gradient(135deg, #b8860b, #daa520); color: #000; padding: 20px 30px; }
  .header h1 { font-size: 24px; }
  .quick-stats { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; }
  .stat-box { background: rgba(0,0,0,0.2); border-radius: 6px; padding: 8px 14px; font-size: 13px; }
  .stat-box .num { font-size: 20px; font-weight: 700; display: block; }
  .tabs { display: flex; background: #1a1d27; border-bottom: 2px solid #b8860b; }
  .tab { padding: 12px 24px; cursor: pointer; font-size: 14px; color: #999; border: none; background: none; }
  .tab.active { color: #daa520; border-bottom: 2px solid #daa520; margin-bottom: -2px; }
  .tab:hover { color: #e0e0e0; }
  .tab-content { display: none; } .tab-content.active { display: block; }
  .filters { padding: 15px 30px; background: #1a1d27; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #2a2d37; }
  .filters label { font-size: 13px; color: #999; }
  .filters select, .filters input { background: #252830; border: 1px solid #3a3d47; color: #e0e0e0; padding: 6px 10px; border-radius: 4px; font-size: 13px; }
  .filters button { background: #b8860b; color: #000; border: none; padding: 7px 16px; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 13px; }
  .filters button:hover { background: #daa520; }
  .filters .export { background: #2a5; color: #fff; margin-left: auto; }
  .container { padding: 20px 30px; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { background: #1a1d27; padding: 10px 8px; text-align: left; border-bottom: 2px solid #b8860b; position: sticky; top: 0; }
  td { padding: 8px; border-bottom: 1px solid #2a2d37; vertical-align: top; }
  tr:hover { background: #1a1d27; }
  .score { display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 50%; font-weight: 700; font-size: 12px; }
  .s-high { background: #2a5; color: #fff; } .s-med { background: #b8860b; color: #000; } .s-low { background: #555; color: #ccc; }
  .content { max-width: 350px; max-height: 80px; overflow: hidden; text-overflow: ellipsis; font-size: 12px; color: #aaa; }
  a { color: #daa520; text-decoration: none; } a:hover { text-decoration: underline; }
  .btn-sm { padding: 3px 10px; border: 1px solid #3a3d47; border-radius: 3px; background: transparent; color: #e0e0e0; cursor: pointer; font-size: 12px; }
  .btn-sm:hover { background: #2a2d37; }
  .contacted { color: #2a5; } .not-contacted { color: #888; }
  .empty { text-align: center; padding: 60px; color: #666; font-size: 16px; }
  .modal-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:1000; justify-content:center; align-items:center; }
  .modal-overlay.show { display:flex; }
  .modal { background:#1a1d27; border:1px solid #b8860b; border-radius:8px; padding:24px; max-width:600px; width:90%; max-height:80vh; overflow-y:auto; }
  .modal h3 { color:#daa520; margin-bottom:12px; }
  .modal textarea { width:100%; min-height:200px; background:#252830; color:#e0e0e0; border:1px solid #3a3d47; border-radius:4px; padding:10px; font-size:13px; font-family:inherit; resize:vertical; }
  .modal .btn-copy { background:#2a5; color:#fff; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:600; margin-top:8px; }
  .modal .btn-close { background:#555; color:#fff; border:none; padding:8px 16px; border-radius:4px; cursor:pointer; margin-top:8px; margin-left:8px; }
  .notes-input { background: #252830; border: 1px solid #3a3d47; color: #e0e0e0; padding: 4px 6px; border-radius: 3px; font-size: 12px; width: 140px; }
  .notes-save { padding: 2px 8px; font-size: 11px; background: #b8860b; border: none; color: #000; border-radius: 3px; cursor: pointer; margin-left: 4px; }
  @media (max-width: 768px) {
    .header { padding: 15px; }
    .quick-stats { gap: 8px; }
    .stat-box { padding: 6px 10px; font-size: 12px; }
    .stat-box .num { font-size: 16px; }
    .filters { padding: 10px 15px; }
    .container { padding: 10px 15px; }
    table { font-size: 12px; }
    .content { max-width: 200px; }
    .notes-input { width: 100px; }
    .tabs { overflow-x: auto; }
    .tab { padding: 10px 16px; white-space: nowrap; }
  }
</style>
</head>
<body>
<div class="header">
  <h1>⛏️ Gold Rush Scanner</h1>
  <div class="quick-stats">
    <div class="stat-box"><span class="num">{{ stats.total }}</span>Total Leads</div>
    <div class="stat-box"><span class="num">{{ stats.today }}</span>Today</div>
    <div class="stat-box"><span class="num">{{ stats.avg_score }}</span>Avg Score</div>
    <div class="stat-box"><span class="num">r/{{ stats.top_subreddit }}</span>Top Source</div>
    <div class="stat-box"><span class="num">{{ stats.high_intent }}</span>High Intent</div>
    <div class="stat-box"><span class="num">{{ stats.form_leads }}</span>Form Leads</div>
    <div class="stat-box"><a href="/report" style="color:#000;text-decoration:none;font-weight:700">📊 Report</a></div>
    <div class="stat-box" style="margin-left:auto">
      {% if scan_status.running %}
        <span class="num">⏳</span>Scanning...
      {% else %}
        <form method="post" action="/scan" style="display:inline">
          <button style="background:#2a5;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:700;font-size:14px">🚀 Run Scan</button>
        </form>
        {% if scan_status.last_run %}<br><span style="font-size:11px;color:#666">Last: {{ scan_status.last_run }} ({{ scan_status.last_count }} leads)</span>{% endif %}
      {% endif %}
    </div>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('scanner')">🔍 Scanner Leads</button>
  <button class="tab" onclick="switchTab('form')">📋 Form Submissions</button>
</div>

<div id="tab-scanner" class="tab-content active">
<form class="filters" method="get" action="/">
  <label>Min Score</label>
  <select name="min_score">
    <option value="">All</option>
    {% for i in range(1, 11) %}<option value="{{ i }}" {{ 'selected' if min_score == i }}>≥ {{ i }}</option>{% endfor %}
  </select>
  <label>Subreddit</label>
  <select name="subreddit">
    <option value="">All</option>
    {% for s in subreddits %}<option value="{{ s }}" {{ 'selected' if subreddit == s }}>r/{{ s }}</option>{% endfor %}
  </select>
  <label>From</label>
  <input type="date" name="date_from" value="{{ date_from or '' }}">
  <label>Status</label>
  <select name="contacted">
    <option value="">All</option>
    <option value="0" {{ 'selected' if contacted == '0' }}>Not contacted</option>
    <option value="1" {{ 'selected' if contacted == '1' }}>Contacted</option>
  </select>
  <button type="submit">Filter</button>
  <a href="/export?{{ request.query_string.decode() }}"><button type="button" class="export">📥 Export CSV</button></a>
</form>
<div class="container">
{% if leads %}
<table>
<thead><tr><th>Score</th><th>User</th><th>Source</th><th>Content</th><th>Found</th><th>Notes</th><th>Status</th><th></th></tr></thead>
<tbody>
{% for l in leads %}
<tr>
  <td><span class="score {{ 's-high' if l.intent_score >= 7 else 's-med' if l.intent_score >= 4 else 's-low' }}">{{ l.intent_score }}</span></td>
  <td><a href="https://reddit.com/u/{{ l.username }}" target="_blank">u/{{ l.username }}</a></td>
  <td>{{ l.platform }}/{{ l.subreddit }}</td>
  <td class="content"><a href="{{ l.url }}" target="_blank">{{ l.content[:200] }}</a></td>
  <td style="white-space:nowrap">{{ l.found_at[:10] }}</td>
  <td>
    <form method="post" action="/notes/{{ l.id }}" style="display:inline-flex;align-items:center">
      <input class="notes-input" name="notes" value="{{ l.notes }}" placeholder="Add note...">
      <button class="notes-save" type="submit">💾</button>
    </form>
  </td>
  <td>{% if l.contacted %}<span class="contacted">✅</span>{% else %}<span class="not-contacted">—</span>{% endif %}</td>
  <td>
    <form method="post" action="/toggle/{{ l.id }}" style="display:inline"><button class="btn-sm">{{ '↩' if l.contacted else '✓' }}</button></form>
    <button class="btn-sm" onclick="draftReply({{ l.id }}, '{{ l.username }}', '{{ l.subreddit }}', {{ l.intent_score }})" title="Draft Reply">📝</button>
  </td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty">No leads found. Run the scanner first!<br><code>python scanner.py</code></div>
{% endif %}
</div>
</div>

<div id="tab-form" class="tab-content">
<div class="container">
{% if form_leads %}
<table>
<thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Interest</th><th>Budget</th><th>Source</th><th>Date</th><th>Notes</th><th>Status</th><th></th></tr></thead>
<tbody>
{% for l in form_leads %}
<tr>
  <td>{{ l.name }}</td>
  <td><a href="mailto:{{ l.email }}">{{ l.email }}</a></td>
  <td>{{ l.phone }}</td>
  <td>{{ l.interest }}</td>
  <td>{{ l.budget }}</td>
  <td>{{ l.referral_source }}</td>
  <td style="white-space:nowrap">{{ l.submitted_at[:10] }}</td>
  <td>
    <form method="post" action="/form-notes/{{ l.id }}" style="display:inline-flex;align-items:center">
      <input class="notes-input" name="notes" value="{{ l.notes }}" placeholder="Add note...">
      <button class="notes-save" type="submit">💾</button>
    </form>
  </td>
  <td>{% if l.contacted %}<span class="contacted">✅</span>{% else %}<span class="not-contacted">—</span>{% endif %}</td>
  <td><form method="post" action="/form-toggle/{{ l.id }}" style="display:inline"><button class="btn-sm">{{ '↩' if l.contacted else '✓' }}</button></form></td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty">No form submissions yet. Share your landing page to collect leads!</div>
{% endif %}
</div>
</div>

<div class="modal-overlay" id="replyModal">
  <div class="modal">
    <h3>📝 Draft Reply for <span id="replyUser"></span></h3>
    <textarea id="replyText" readonly></textarea>
    <div>
      <button class="btn-copy" onclick="copyReply()">📋 Copy to Clipboard</button>
      <button class="btn-close" onclick="closeReplyModal()">Close</button>
    </div>
  </div>
</div>

<script>
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

function draftReply(leadId, username, subreddit, score) {
  fetch('/api/draft-reply', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({lead_id: leadId, username: username, subreddit: subreddit, score: score})
  })
  .then(r => r.json())
  .then(data => {
    document.getElementById('replyUser').textContent = 'u/' + username;
    document.getElementById('replyText').value = data.reply;
    document.getElementById('replyModal').classList.add('show');
  });
}

function closeReplyModal() {
  document.getElementById('replyModal').classList.remove('show');
}

function copyReply() {
  const ta = document.getElementById('replyText');
  ta.select();
  navigator.clipboard.writeText(ta.value);
}

document.getElementById('replyModal').addEventListener('click', function(e) {
  if (e.target === this) closeReplyModal();
});
</script>
</body></html>"""


@app.route("/")
def index():
    min_score = request.args.get("min_score", type=int)
    subreddit = request.args.get("subreddit") or None
    date_from = request.args.get("date_from") or None
    contacted = request.args.get("contacted")
    contacted_bool = None if not contacted else contacted == "1"

    leads = get_leads(min_score=min_score, subreddit=subreddit, date_from=date_from, contacted=contacted_bool)
    return render_template_string(
        TEMPLATE,
        leads=leads, form_leads=get_form_leads(), stats=get_stats(), subreddits=get_subreddits(),
        min_score=min_score, subreddit=subreddit, date_from=date_from, contacted=contacted,
        scan_status=_scan_status, request=request,
    )


@app.route("/scan", methods=["POST"])
def trigger_scan():
    if not _scan_status["running"]:
        t = threading.Thread(target=_run_scan_bg, daemon=True)
        t.start()
    return redirect(url_for("index"))


@app.route("/toggle/<int:lead_id>", methods=["POST"])
def toggle(lead_id):
    mark_contacted(lead_id)
    return redirect(request.referrer or url_for("index"))


@app.route("/notes/<int:lead_id>", methods=["POST"])
def save_notes(lead_id):
    update_notes(lead_id, request.form.get("notes", ""))
    return redirect(request.referrer or url_for("index"))


@app.route("/form-notes/<int:lead_id>", methods=["POST"])
def save_form_notes(lead_id):
    update_form_lead_notes(lead_id, request.form.get("notes", ""))
    return redirect(request.referrer or url_for("index"))


@app.route("/form-toggle/<int:lead_id>", methods=["POST"])
def form_toggle(lead_id):
    mark_form_lead_contacted(lead_id)
    return redirect(request.referrer or url_for("index"))


@app.route("/api/submit-lead", methods=["POST"])
def submit_lead():
    """Endpoint for landing page form submissions."""
    data = request.get_json() if request.is_json else request.form
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    interest = data.get("interest", "").strip()
    budget = data.get("budget", "").strip()
    referral = data.get("referral_source", "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    insert_form_lead(name, email, phone, interest, budget, referral)

    # Send notification
    try:
        from notifications import notify_form_submission
        notify_form_submission(name, email, phone, interest, budget, referral)
    except Exception:
        pass

    return jsonify({"success": True, "message": "Thank you! We'll be in touch shortly."})


@app.route("/api/draft-reply", methods=["POST"])
def draft_reply():
    """Generate a draft reply for a lead."""
    data = request.get_json()
    lead_id = data.get("lead_id")
    username = data.get("username", "")
    subreddit = data.get("subreddit", "")
    score = data.get("score", 5)

    # Get the lead content from DB
    from db import get_connection
    conn = get_connection()
    row = conn.execute("SELECT content FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    content = row["content"] if row else ""

    reply = generate_reply(username, content, subreddit, score)
    return jsonify({"reply": reply})


@app.route("/report")
def weekly_report():
    """Show the weekly report."""
    report = generate_weekly_report()
    return report["html"]


@app.route("/landing")
@app.route("/apply")
def landing_page():
    return send_from_directory(os.path.join(app.root_path, "landing"), "index.html")


@app.route("/export")
def export():
    min_score = request.args.get("min_score", type=int)
    subreddit = request.args.get("subreddit") or None
    date_from = request.args.get("date_from") or None
    contacted = request.args.get("contacted")
    contacted_bool = None if not contacted else contacted == "1"

    leads = get_leads(min_score=min_score, subreddit=subreddit, date_from=date_from, contacted=contacted_bool)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["id", "platform", "username", "content", "url", "subreddit", "intent_score", "found_at", "contacted", "notes"])
    writer.writeheader()
    writer.writerows(leads)
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=leads.csv"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"🚀 Dashboard running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
