#!/usr/bin/env python3
"""Flask dashboard for viewing and managing leads."""

import csv
import io
import os
import threading
import time as _time
from flask import Flask, render_template_string, request, redirect, url_for, Response, jsonify, send_from_directory

from config import DASHBOARD_HOST, DASHBOARD_PORT, COMPANY_NAME, BRAND_COLOR
from db import (
    get_leads, mark_contacted, get_subreddits, get_stats,
    update_notes, insert_form_lead, get_form_leads,
    update_form_lead_notes, mark_form_lead_contacted,
    get_queue_items, get_queue_stats, update_queue_status, add_to_queue,
    leads_by_day, leads_by_subreddit, leads_score_distribution,
    leads_by_platform, leads_by_hour, leads_by_keyword, get_analytics_stats,
    get_platforms,
)
from templates import generate_reply
from competitors import get_competitor_leads, get_competitor_stats
from reports import generate_weekly_report
from reply_queue import approve_reply, skip_reply, reddit_configured, start_poster_thread

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

# Start reply poster thread
start_poster_thread()

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
  <h1>⛏️ {{ company_name if company_name != '[Company Name]' else 'Gold Rush Scanner' }}</h1>
  <div class="quick-stats">
    <div class="stat-box"><span class="num">{{ stats.total }}</span>Total Leads</div>
    <div class="stat-box"><span class="num">{{ stats.today }}</span>Today</div>
    <div class="stat-box"><span class="num">{{ stats.avg_score }}</span>Avg Score</div>
    <div class="stat-box"><span class="num">r/{{ stats.top_subreddit }}</span>Top Source</div>
    <div class="stat-box"><span class="num">{{ stats.high_intent }}</span>High Intent</div>
    <div class="stat-box"><span class="num">{{ stats.form_leads }}</span>Form Leads</div>
    <div class="stat-box"><a href="/report" style="color:#000;text-decoration:none;font-weight:700">📊 Report</a></div>
    <div class="stat-box"><a href="/analytics" style="color:#000;text-decoration:none;font-weight:700">📈 Analytics</a></div>
    <div class="stat-box"><a href="/roi" style="color:#000;text-decoration:none;font-weight:700">💰 ROI</a></div>
    <div class="stat-box"><a href="/pitch" style="color:#000;text-decoration:none;font-weight:700">📊 Pitch Deck</a></div>
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
  <button class="tab" onclick="switchTab('competitors')">🎯 Competitor Leads{% if comp_stats.complaints %} <span style="background:#d9534f;color:#fff;border-radius:10px;padding:1px 7px;font-size:11px;margin-left:4px">{{ comp_stats.complaints }}</span>{% endif %}</button>
  <button class="tab" onclick="switchTab('form')">📋 Form Submissions</button>
  <button class="tab" onclick="switchTab('queue')">📤 Reply Queue{% if queue_stats.pending %} <span style="background:#b8860b;color:#000;border-radius:10px;padding:1px 7px;font-size:11px;margin-left:4px">{{ queue_stats.pending }}</span>{% endif %}</button>
</div>

<div id="tab-scanner" class="tab-content active">
<form class="filters" method="get" action="/">
  <label>Min Score</label>
  <select name="min_score">
    <option value="">All</option>
    {% for i in range(1, 11) %}<option value="{{ i }}" {{ 'selected' if min_score == i }}>≥ {{ i }}</option>{% endfor %}
  </select>
  <label>Source</label>
  <select name="subreddit">
    <option value="">All</option>
    {% for s in subreddits %}<option value="{{ s }}" {{ 'selected' if subreddit == s }}>{{ s }}</option>{% endfor %}
  </select>
  <label>Platform</label>
  <select name="platform">
    <option value="">All</option>
    {% for p in platforms %}<option value="{{ p }}" {{ 'selected' if platform == p }}>{{ p|capitalize }}</option>{% endfor %}
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

<div id="tab-competitors" class="tab-content">
<div class="container">
  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px">
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#d9534f">{{ comp_stats.complaints }}</span>Complaints</div>
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#f0ad4e">{{ comp_stats.mentions }}</span>Mentions</div>
  </div>
  <p style="color:#999;font-size:13px;margin-bottom:16px">🎯 These are people unhappy with competitors — high-value leads ready to switch. Monitoring: APMEX, JM Bullion, SD Bullion, Money Metals, Goldco, Birch Gold, Augusta Precious Metals, Noble Gold.</p>
{% if comp_leads %}
<table>
<thead><tr><th>Score</th><th>User</th><th>Source</th><th>Content</th><th>Found</th><th>Notes</th><th>Status</th><th></th></tr></thead>
<tbody>
{% for l in comp_leads %}
<tr style="{% if 'competitor_complaint' in (l.notes or '') %}background:#2a1a1a{% endif %}">
  <td><span class="score s-high">{{ l.intent_score }}</span></td>
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
  </td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<div class="empty">No competitor complaints found yet. Run the scanner to start monitoring!</div>
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

<div id="tab-queue" class="tab-content">
<div class="container">
  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px">
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#daa520">{{ queue_stats.pending }}</span>Pending</div>
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#f0ad4e">{{ queue_stats.approved }}</span>Approved</div>
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#2a5">{{ queue_stats.posted_today }}</span>Posted Today</div>
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#2a5">{{ queue_stats.total_posted }}</span>Total Posted</div>
    <div class="stat-box" style="background:#2a2d37"><span class="num" style="color:#d9534f">{{ queue_stats.failed }}</span>Failed</div>
    {% if not reddit_configured %}
    <div style="background:#3a2a0a;border:1px solid #b8860b;border-radius:6px;padding:10px 16px;font-size:13px;color:#daa520;display:flex;align-items:center;gap:8px">
      ⚠️ Reddit credentials not configured — replies can be queued but not auto-posted. Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD in config.py
    </div>
    {% endif %}
  </div>
  {% if queue_items %}
  {% for item in queue_items %}
  <div style="background:#1a1d27;border:1px solid #2a2d37;border-radius:8px;padding:16px;margin-bottom:12px;{% if item.status == 'pending' %}border-left:3px solid #f0ad4e{% elif item.status == 'posted' %}border-left:3px solid #2a5{% elif item.status == 'failed' %}border-left:3px solid #d9534f{% elif item.status == 'approved' %}border-left:3px solid #5bc0de{% else %}border-left:3px solid #555{% endif %}">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <div>
        <span style="font-weight:700;color:#daa520">u/{{ item.username or 'unknown' }}</span>
        <span style="color:#666;font-size:12px;margin-left:8px">r/{{ item.subreddit or '?' }}</span>
        {% if item.intent_score %}<span class="score {{ 's-high' if item.intent_score >= 7 else 's-med' if item.intent_score >= 4 else 's-low' }}" style="margin-left:8px">{{ item.intent_score }}</span>{% endif %}
      </div>
      <div>
        {% if item.status == 'pending' %}<span style="background:#f0ad4e;color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">Pending</span>
        {% elif item.status == 'approved' %}<span style="background:#5bc0de;color:#000;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">Approved</span>
        {% elif item.status == 'posted' %}<span style="background:#2a5;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">✅ Posted</span>
        {% elif item.status == 'skipped' %}<span style="background:#555;color:#ccc;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">Skipped</span>
        {% elif item.status == 'failed' %}<span style="background:#d9534f;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600">❌ Failed</span>{% endif %}
        <span style="color:#666;font-size:11px;margin-left:8px">{{ item.created_at[:16] }}</span>
      </div>
    </div>
    <div style="background:#252830;border-radius:4px;padding:10px;font-size:12px;color:#aaa;margin-bottom:10px;max-height:60px;overflow:hidden">
      <strong style="color:#888">Original:</strong> {{ (item.lead_content or '')[:300] }}
    </div>
    {% if item.status in ('pending', 'failed') %}
    <form method="post" action="/queue/approve/{{ item.id }}">
      <textarea name="reply_text" style="width:100%;min-height:100px;background:#252830;color:#e0e0e0;border:1px solid #3a3d47;border-radius:4px;padding:10px;font-size:13px;font-family:inherit;resize:vertical;margin-bottom:8px">{{ item.reply_text }}</textarea>
      <div style="display:flex;gap:8px">
        <button type="submit" style="background:#2a5;color:#fff;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:600;font-size:13px">✅ Approve & Post</button>
        <button type="submit" formaction="/queue/skip/{{ item.id }}" style="background:#555;color:#ccc;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-size:13px">⏭️ Skip</button>
        <a href="{{ item.target_url }}" target="_blank" style="padding:8px 16px;font-size:13px;color:#daa520;display:flex;align-items:center">🔗 View on Reddit</a>
      </div>
    </form>
    {% elif item.status == 'posted' %}
    <div style="font-size:12px;color:#888;white-space:pre-wrap;max-height:80px;overflow:hidden">{{ item.reply_text[:300] }}</div>
    {% if item.posted_at %}<div style="font-size:11px;color:#666;margin-top:4px">Posted: {{ item.posted_at[:16] }}</div>{% endif %}
    {% elif item.status == 'approved' %}
    <div style="font-size:12px;color:#5bc0de;white-space:pre-wrap;max-height:80px;overflow:hidden">{{ item.reply_text[:300] }}</div>
    <div style="font-size:11px;color:#666;margin-top:4px">⏳ Waiting to post (rate limited)...</div>
    {% else %}
    <div style="font-size:12px;color:#888;white-space:pre-wrap;max-height:80px;overflow:hidden">{{ item.reply_text[:300] }}</div>
    {% endif %}
    {% if item.error_message %}<div style="font-size:11px;color:#d9534f;margin-top:4px">Error: {{ item.error_message }}</div>{% endif %}
  </div>
  {% endfor %}
  {% else %}
  <div class="empty">No replies in queue yet. High-intent leads (score ≥ 7) are auto-queued during scans.</div>
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
    platform = request.args.get("platform") or None
    contacted_bool = None if not contacted else contacted == "1"

    leads = get_leads(min_score=min_score, subreddit=subreddit, date_from=date_from, contacted=contacted_bool, platform=platform)
    return render_template_string(
        TEMPLATE,
        leads=leads, form_leads=get_form_leads(), stats=get_stats(), subreddits=get_subreddits(),
        platforms=get_platforms(),
        min_score=min_score, subreddit=subreddit, date_from=date_from, contacted=contacted,
        platform=platform,
        scan_status=_scan_status, request=request,
        queue_items=get_queue_items(), queue_stats=get_queue_stats(),
        reddit_configured=reddit_configured(),
        company_name=COMPANY_NAME,
        comp_leads=get_competitor_leads(), comp_stats=get_competitor_stats(),
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


@app.route("/queue/approve/<int:queue_id>", methods=["POST"])
def queue_approve(queue_id):
    reply_text = request.form.get("reply_text", "").strip()
    if reply_text:
        from db import get_connection
        conn = get_connection()
        conn.execute("UPDATE reply_queue SET reply_text = ? WHERE id = ?", (reply_text, queue_id))
        conn.commit()
        conn.close()
    approve_reply(queue_id)
    return redirect(url_for("index") + "#tab-queue")


@app.route("/queue/skip/<int:queue_id>", methods=["POST"])
def queue_skip(queue_id):
    skip_reply(queue_id)
    return redirect(url_for("index") + "#tab-queue")


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


# --- Analytics Dashboard ---
ANALYTICS_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Analytics — {{ company_name }}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; }
  .header { background: linear-gradient(135deg, #b8860b, #daa520); color: #000; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 24px; }
  .header nav a { color: #000; text-decoration: none; font-weight: 600; margin-left: 16px; padding: 6px 14px; border-radius: 4px; background: rgba(0,0,0,0.15); }
  .header nav a:hover { background: rgba(0,0,0,0.3); }
  .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; padding: 24px 30px; }
  .metric { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 8px; padding: 20px; text-align: center; }
  .metric .value { font-size: 32px; font-weight: 700; color: #daa520; }
  .metric .label { font-size: 13px; color: #888; margin-top: 4px; }
  .metric .change { font-size: 13px; margin-top: 4px; }
  .change.up { color: #2a5; } .change.down { color: #d9534f; }
  .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; padding: 0 30px 30px; }
  .chart-card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 8px; padding: 20px; }
  .chart-card h3 { color: #daa520; font-size: 15px; margin-bottom: 12px; }
  @media (max-width: 768px) { .charts { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="header">
  <h1>📈 Analytics Dashboard</h1>
  <nav><a href="/">← Dashboard</a><a href="/roi">💰 ROI</a><a href="/pitch">📊 Pitch</a></nav>
</div>

<div class="metrics">
  <div class="metric"><div class="value">{{ stats.total }}</div><div class="label">Total Leads (All Time)</div></div>
  <div class="metric">
    <div class="value">{{ stats.this_week }}</div><div class="label">Leads This Week</div>
    <div class="change {{ 'up' if stats.week_change >= 0 else 'down' }}">
      {{ '▲' if stats.week_change >= 0 else '▼' }} {{ stats.week_change }}% vs last week ({{ stats.last_week }})
    </div>
  </div>
  <div class="metric"><div class="value">{{ stats.avg_score }}</div><div class="label">Average Intent Score</div></div>
  <div class="metric"><div class="value">{{ stats.high_intent_week }}</div><div class="label">High Intent (8+) This Week</div></div>
  <div class="metric"><div class="value">{{ stats.form_conversion_rate }}%</div><div class="label">Form Conversion Rate</div></div>
  <div class="metric"><div class="value">${{ estimated_value }}</div><div class="label">Est. Lead Value (Monthly)</div></div>
</div>

<div class="charts">
  <div class="chart-card"><h3>Leads Over Time (Last 30 Days)</h3><canvas id="leadsTime"></canvas></div>
  <div class="chart-card"><h3>Leads by Subreddit</h3><canvas id="leadsSub"></canvas></div>
  <div class="chart-card"><h3>Score Distribution</h3><canvas id="scoreDist"></canvas></div>
  <div class="chart-card"><h3>Leads by Platform</h3><canvas id="leadsPlatform"></canvas></div>
  <div class="chart-card"><h3>Peak Posting Hours (UTC)</h3><canvas id="leadsHour"></canvas></div>
  <div class="chart-card"><h3>Top Keywords</h3><canvas id="leadsKeyword"></canvas></div>
</div>

<script>
const gold = '#daa520', darkGold = '#b8860b', gridColor = '#2a2d37', textColor = '#888';
const defaultOpts = { responsive: true, plugins: { legend: { labels: { color: textColor } } }, scales: { x: { ticks: { color: textColor }, grid: { color: gridColor } }, y: { ticks: { color: textColor }, grid: { color: gridColor } } } };

// Leads over time
new Chart(document.getElementById('leadsTime'), {
  type: 'line', data: {
    labels: {{ days_labels | tojson }}, datasets: [{ label: 'Leads', data: {{ days_values | tojson }}, borderColor: gold, backgroundColor: 'rgba(218,165,32,0.1)', fill: true, tension: 0.3 }]
  }, options: defaultOpts
});

// Leads by subreddit
new Chart(document.getElementById('leadsSub'), {
  type: 'bar', data: {
    labels: {{ sub_labels | tojson }}, datasets: [{ label: 'Leads', data: {{ sub_values | tojson }}, backgroundColor: gold }]
  }, options: { ...defaultOpts, indexAxis: 'y' }
});

// Score distribution
new Chart(document.getElementById('scoreDist'), {
  type: 'bar', data: {
    labels: {{ score_labels | tojson }}, datasets: [{ label: 'Leads', data: {{ score_values | tojson }}, backgroundColor: {{ score_colors | tojson }} }]
  }, options: defaultOpts
});

// Leads by platform
new Chart(document.getElementById('leadsPlatform'), {
  type: 'doughnut', data: {
    labels: {{ platform_labels | tojson }}, datasets: [{ data: {{ platform_values | tojson }}, backgroundColor: ['#daa520','#b8860b','#8b6914','#cd950c','#ffd700','#c4a035'] }]
  }, options: { responsive: true, plugins: { legend: { labels: { color: textColor } } } }
});

// Peak hours
new Chart(document.getElementById('leadsHour'), {
  type: 'bar', data: {
    labels: {{ hour_labels | tojson }}, datasets: [{ label: 'Leads', data: {{ hour_values | tojson }}, backgroundColor: darkGold }]
  }, options: defaultOpts
});

// Top keywords
new Chart(document.getElementById('leadsKeyword'), {
  type: 'bar', data: {
    labels: {{ kw_labels | tojson }}, datasets: [{ label: 'Leads', data: {{ kw_values | tojson }}, backgroundColor: gold }]
  }, options: { ...defaultOpts, indexAxis: 'y' }
});
</script>
</body></html>"""


@app.route("/analytics")
def analytics():
    stats = get_analytics_stats()
    by_day = leads_by_day()
    by_sub = leads_by_subreddit()
    score_dist = leads_score_distribution()
    by_platform = leads_by_platform()
    by_hour = leads_by_hour()
    by_kw = leads_by_keyword()

    # Estimated value: leads_this_month * 3% conversion * $5000 avg deal
    estimated_value = f"{stats['leads_this_month'] * 0.03 * 5000:,.0f}"

    score_colors = []
    for s in score_dist:
        sc = s["score"]
        if sc >= 7:
            score_colors.append("#2a5")
        elif sc >= 4:
            score_colors.append("#b8860b")
        else:
            score_colors.append("#555")

    # Fill in 24 hours
    hour_map = {h["hour"]: h["count"] for h in by_hour}
    hour_labels = [f"{h:02d}:00" for h in range(24)]
    hour_values = [hour_map.get(h, 0) for h in range(24)]

    return render_template_string(
        ANALYTICS_TEMPLATE,
        stats=stats,
        company_name=COMPANY_NAME,
        estimated_value=estimated_value,
        days_labels=[d["day"] for d in by_day],
        days_values=[d["count"] for d in by_day],
        sub_labels=[s["subreddit"] for s in by_sub],
        sub_values=[s["count"] for s in by_sub],
        score_labels=[s["score"] for s in score_dist],
        score_values=[s["count"] for s in score_dist],
        score_colors=score_colors,
        platform_labels=[p["platform"] for p in by_platform],
        platform_values=[p["count"] for p in by_platform],
        hour_labels=hour_labels,
        hour_values=hour_values,
        kw_labels=[k["keyword"] for k in by_kw],
        kw_values=[k["count"] for k in by_kw],
    )


# --- ROI Calculator ---
ROI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ROI Calculator — {{ company_name }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; }
  .header { background: linear-gradient(135deg, #b8860b, #daa520); color: #000; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 24px; }
  .header nav a { color: #000; text-decoration: none; font-weight: 600; margin-left: 16px; padding: 6px 14px; border-radius: 4px; background: rgba(0,0,0,0.15); }
  .header nav a:hover { background: rgba(0,0,0,0.3); }
  .container { max-width: 900px; margin: 30px auto; padding: 0 30px; }
  .card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 12px; padding: 30px; margin-bottom: 24px; }
  .card h2 { color: #daa520; margin-bottom: 20px; font-size: 20px; }
  .input-group { margin-bottom: 20px; }
  .input-group label { display: block; font-size: 14px; color: #999; margin-bottom: 6px; }
  .input-group input[type="range"] { width: 100%; accent-color: #daa520; }
  .input-group input[type="number"] { background: #252830; border: 1px solid #3a3d47; color: #e0e0e0; padding: 8px 12px; border-radius: 4px; font-size: 16px; width: 200px; }
  .input-group .value { font-size: 20px; font-weight: 700; color: #daa520; }
  .results { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
  .result { background: #252830; border-radius: 8px; padding: 20px; text-align: center; }
  .result .val { font-size: 28px; font-weight: 700; color: #daa520; }
  .result .lbl { font-size: 13px; color: #888; margin-top: 4px; }
  .result.highlight { border: 2px solid #daa520; }
  .bar { height: 24px; border-radius: 4px; margin-top: 12px; transition: width 0.3s; }
</style>
</head>
<body>
<div class="header">
  <h1>💰 ROI Calculator</h1>
  <nav><a href="/">← Dashboard</a><a href="/analytics">📈 Analytics</a><a href="/pitch">📊 Pitch</a></nav>
</div>
<div class="container">
  <div class="card">
    <h2>Inputs</h2>
    <div class="input-group">
      <label>Monthly Tool Cost ($)</label>
      <input type="number" id="cost" value="500" min="0" step="50" oninput="calc()">
    </div>
    <div class="input-group">
      <label>Average Deal Size ($): <span class="value" id="dealVal">$5,000</span></label>
      <input type="range" id="deal" min="500" max="50000" step="500" value="5000" oninput="calc()">
    </div>
    <div class="input-group">
      <label>Conversion Rate (%): <span class="value" id="convVal">3.0%</span></label>
      <input type="range" id="conv" min="0.5" max="10" step="0.5" value="3" oninput="calc()">
    </div>
    <div class="input-group">
      <label>Leads Per Month (from your data: {{ leads_month }})</label>
      <input type="number" id="leads" value="{{ leads_month }}" min="0" oninput="calc()">
    </div>
  </div>
  <div class="card">
    <h2>Results</h2>
    <div class="results">
      <div class="result highlight"><div class="val" id="roi">—</div><div class="lbl">ROI %</div></div>
      <div class="result"><div class="val" id="revenue">—</div><div class="lbl">Est. Monthly Revenue</div></div>
      <div class="result"><div class="val" id="rpl">—</div><div class="lbl">Revenue Per Lead</div></div>
      <div class="result"><div class="val" id="breakeven">—</div><div class="lbl">Break-Even Leads</div></div>
      <div class="result"><div class="val" id="profit">—</div><div class="lbl">Monthly Profit</div></div>
    </div>
    <div style="margin-top:24px">
      <div style="display:flex;justify-content:space-between;font-size:13px;color:#888"><span>Cost</span><span>Revenue</span></div>
      <div style="background:#252830;border-radius:4px;overflow:hidden;height:28px;position:relative;margin-top:4px">
        <div class="bar" id="costBar" style="background:#d9534f;position:absolute;left:0;top:0;height:100%"></div>
        <div class="bar" id="revBar" style="background:#2a5;position:absolute;left:0;top:0;height:100%"></div>
      </div>
    </div>
  </div>
</div>
<script>
function calc() {
  const cost = +document.getElementById('cost').value;
  const deal = +document.getElementById('deal').value;
  const conv = +document.getElementById('conv').value / 100;
  const leads = +document.getElementById('leads').value;
  document.getElementById('dealVal').textContent = '$' + deal.toLocaleString();
  document.getElementById('convVal').textContent = (conv*100).toFixed(1) + '%';
  const revenue = leads * conv * deal;
  const profit = revenue - cost;
  const roiPct = cost > 0 ? ((revenue - cost) / cost * 100) : 0;
  const rpl = leads > 0 ? revenue / leads : 0;
  const breakeven = (conv * deal) > 0 ? Math.ceil(cost / (conv * deal)) : 0;
  document.getElementById('roi').textContent = roiPct.toFixed(0) + '%';
  document.getElementById('revenue').textContent = '$' + revenue.toLocaleString(undefined, {maximumFractionDigits:0});
  document.getElementById('rpl').textContent = '$' + rpl.toFixed(2);
  document.getElementById('breakeven').textContent = breakeven;
  document.getElementById('profit').textContent = (profit>=0?'':'−$') + (profit>=0?'$':'') + Math.abs(profit).toLocaleString(undefined,{maximumFractionDigits:0});
  document.getElementById('profit').style.color = profit >= 0 ? '#2a5' : '#d9534f';
  const maxVal = Math.max(cost, revenue, 1);
  document.getElementById('costBar').style.width = (cost/maxVal*100) + '%';
  document.getElementById('revBar').style.width = (revenue/maxVal*100) + '%';
}
calc();
</script>
</body></html>"""


@app.route("/roi")
def roi():
    stats = get_analytics_stats()
    return render_template_string(ROI_TEMPLATE, company_name=COMPANY_NAME, leads_month=stats["leads_this_month"])


# --- Pitch Deck ---
PITCH_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pitch Deck — {{ company_name }}</title>
<style>
  @media print { .no-print { display: none !important; } .page { break-after: page; } body { background: #fff; } }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Georgia', 'Times New Roman', serif; background: #0f1117; color: #222; }
  .no-print { background: linear-gradient(135deg, #b8860b, #daa520); color: #000; padding: 14px 30px; display: flex; justify-content: space-between; align-items: center; }
  .no-print a { color: #000; text-decoration: none; font-weight: 600; margin-left: 16px; padding: 6px 14px; border-radius: 4px; background: rgba(0,0,0,0.15); }
  .no-print button { background: #000; color: #daa520; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; font-weight: 700; font-size: 14px; }
  .page { max-width: 900px; margin: 0 auto; padding: 60px 50px; background: #fff; min-height: 100vh; }
  .page + .page { margin-top: 20px; }
  h1 { font-size: 36px; color: #000; margin-bottom: 8px; }
  h2 { font-size: 24px; color: #b8860b; border-bottom: 2px solid #daa520; padding-bottom: 8px; margin: 40px 0 20px; }
  h3 { font-size: 18px; color: #333; margin: 20px 0 10px; }
  p, li { font-size: 16px; line-height: 1.7; color: #444; }
  ul { margin-left: 24px; margin-bottom: 16px; }
  .cover { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; min-height: 80vh; }
  .cover h1 { font-size: 42px; margin-bottom: 12px; }
  .cover .sub { font-size: 20px; color: #b8860b; margin-bottom: 40px; }
  .cover .company { font-size: 16px; color: #888; }
  .flow { display: flex; gap: 12px; align-items: center; justify-content: center; flex-wrap: wrap; margin: 20px 0; }
  .flow .step { background: #f8f4e8; border: 2px solid #daa520; border-radius: 8px; padding: 16px 24px; text-align: center; font-weight: 700; color: #333; }
  .flow .arrow { font-size: 24px; color: #daa520; }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin: 20px 0; }
  .stat-box { background: #f8f4e8; border-left: 4px solid #daa520; padding: 16px; border-radius: 4px; }
  .stat-box .num { font-size: 28px; font-weight: 700; color: #b8860b; }
  .stat-box .lbl { font-size: 13px; color: #666; }
  .score-bar { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
  .score-bar .bar { height: 18px; border-radius: 3px; }
  .score-bar .label { font-size: 13px; min-width: 60px; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #e0d8c0; font-size: 14px; }
  th { background: #f8f4e8; color: #333; font-weight: 700; }
  .placeholder { background: #fff3cd; border: 1px dashed #b8860b; padding: 12px 16px; border-radius: 4px; color: #856404; font-style: italic; margin: 16px 0; }
</style>
</head>
<body>
<div class="no-print">
  <span style="font-weight:700">📊 Pitch Deck</span>
  <div>
    <a href="/">← Dashboard</a>
    <button onclick="window.print()">🖨️ Print / Save PDF</button>
  </div>
</div>

<div class="page cover">
  <h1>Gold Rush Lead Generation Platform</h1>
  <div class="sub">AI-Powered Precious Metals Buyer Discovery</div>
  <div class="company">Presentation for {{ company_name }}</div>
</div>

<div class="page">
  <h2>The Problem</h2>
  <ul>
    <li><strong>Expensive lead generation</strong> — traditional methods cost $50-200+ per lead</li>
    <li><strong>Low quality leads</strong> — most have no real buying intent</li>
    <li><strong>Duplicate contacts</strong> — paying for the same prospects across channels</li>
    <li><strong>Wrong targets</strong> — broad advertising reaches uninterested audiences</li>
    <li><strong>Slow response times</strong> — by the time you find a buyer, they've already purchased</li>
  </ul>

  <h2>The Solution</h2>
  <p>AI-powered social media monitoring that finds <strong>real buyers</strong> actively discussing precious metals purchases — scored by intent level for prioritized outreach.</p>

  <h2>How It Works</h2>
  <div class="flow">
    <div class="step">🔍 Scanner<br><small>Monitor platforms 24/7</small></div>
    <div class="arrow">→</div>
    <div class="step">🎯 Score<br><small>AI intent scoring 1-10</small></div>
    <div class="arrow">→</div>
    <div class="step">📋 Queue<br><small>Review & approve</small></div>
    <div class="arrow">→</div>
    <div class="step">💰 Convert<br><small>Engage & close</small></div>
  </div>
</div>

<div class="page">
  <h2>Real Results</h2>
  <div class="stat-grid">
    <div class="stat-box"><div class="num">{{ stats.total }}</div><div class="lbl">Total Leads Found</div></div>
    <div class="stat-box"><div class="num">{{ stats.avg_score }}</div><div class="lbl">Average Intent Score</div></div>
    <div class="stat-box"><div class="num">{{ stats.high_intent_week }}</div><div class="lbl">High Intent (8+) This Week</div></div>
    <div class="stat-box"><div class="num">{{ stats.this_week }}</div><div class="lbl">Leads This Week</div></div>
    <div class="stat-box"><div class="num">{{ stats.leads_this_month }}</div><div class="lbl">Leads This Month</div></div>
    <div class="stat-box"><div class="num">{{ subreddit_count }}</div><div class="lbl">Subreddits Monitored</div></div>
  </div>

  <h3>Lead Quality — Score Distribution</h3>
  {% for s in score_dist %}
  <div class="score-bar">
    <div class="label">Score {{ s.score }}</div>
    <div class="bar" style="width:{{ (s.count / max_score_count * 400) | int }}px;background:{{ '#2a5' if s.score >= 7 else '#b8860b' if s.score >= 4 else '#888' }}"></div>
    <span style="font-size:13px;color:#666">{{ s.count }}</span>
  </div>
  {% endfor %}

  <h3>Top Sources</h3>
  <table>
    <tr><th>Subreddit</th><th>Leads</th></tr>
    {% for s in top_subs[:8] %}
    <tr><td>r/{{ s.subreddit }}</td><td>{{ s.count }}</td></tr>
    {% endfor %}
  </table>
</div>

<div class="page">
  <h2>Platform Coverage</h2>
  <table>
    <tr><th>Platform</th><th>Status</th><th>Description</th></tr>
    <tr><td>Reddit</td><td>✅ Live</td><td>11+ subreddits, real-time monitoring</td></tr>
    <tr><td>YouTube</td><td>🟡 Ready</td><td>Comment scanning on precious metals videos</td></tr>
    <tr><td>X / Twitter</td><td>🟡 Ready</td><td>Keyword monitoring for buying signals</td></tr>
    <tr><td>Web Forums</td><td>🟡 Ready</td><td>Precious metals community forums</td></tr>
  </table>

  <h2>ROI Projection</h2>
  <table>
    <tr><th>Metric</th><th>Conservative (2%)</th><th>Moderate (3%)</th><th>Optimistic (5%)</th></tr>
    <tr><td>Monthly Leads</td><td>{{ stats.leads_this_month }}</td><td>{{ stats.leads_this_month }}</td><td>{{ stats.leads_this_month }}</td></tr>
    <tr><td>Conversions</td><td>{{ (stats.leads_this_month * 0.02) | round(1) }}</td><td>{{ (stats.leads_this_month * 0.03) | round(1) }}</td><td>{{ (stats.leads_this_month * 0.05) | round(1) }}</td></tr>
    <tr><td>Revenue ($5K avg)</td><td>${{ (stats.leads_this_month * 0.02 * 5000) | int | string }}</td><td>${{ (stats.leads_this_month * 0.03 * 5000) | int | string }}</td><td>${{ (stats.leads_this_month * 0.05 * 5000) | int | string }}</td></tr>
  </table>

  <h2>Pricing</h2>
  <div style="display:flex;gap:24px;flex-wrap:wrap;justify-content:center;margin:20px 0">
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #888;border-radius:12px;padding:24px;text-align:center;background:#1a1a1a">
      <div style="font-size:14px;color:#888;text-transform:uppercase;letter-spacing:2px">🥉 Silver</div>
      <div style="font-size:42px;font-weight:800;color:#c0c0c0;margin:12px 0">$897<span style="font-size:16px;color:#888">/mo</span></div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Reddit monitoring (8 subreddits)</li>
        <li>✅ Up to 200 leads/month</li>
        <li>✅ Intent scoring & deduplication</li>
        <li>✅ Dashboard access</li>
        <li>✅ CSV export</li>
        <li>✅ Email notifications</li>
        <li>❌ Web forum scanning</li>
        <li>❌ Competitor monitoring</li>
        <li>❌ Reply automation</li>
      </ul>
      <div style="margin-top:16px;font-size:12px;color:#666">For dealers getting started with digital leads</div>
    </div>
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #daa520;border-radius:12px;padding:24px;text-align:center;background:#1a1200;position:relative">
      <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#daa520;color:#000;padding:2px 16px;border-radius:20px;font-size:11px;font-weight:700">MOST POPULAR</div>
      <div style="font-size:14px;color:#daa520;text-transform:uppercase;letter-spacing:2px">🥇 Gold</div>
      <div style="font-size:42px;font-weight:800;color:#daa520;margin:12px 0">$1,747<span style="font-size:16px;color:#888">/mo</span></div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Reddit + Web forum monitoring</li>
        <li>✅ Unlimited leads</li>
        <li>✅ Competitor complaint detection</li>
        <li>✅ Reply queue with AI templates</li>
        <li>✅ Branded landing page</li>
        <li>✅ Analytics dashboard</li>
        <li>✅ Weekly performance reports</li>
        <li>✅ Priority support</li>
        <li>❌ X/Twitter & YouTube</li>
      </ul>
      <div style="margin-top:16px;font-size:12px;color:#b8860b">For serious dealers ready to dominate lead gen</div>
    </div>
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #b9f2ff;border-radius:12px;padding:24px;text-align:center;background:#0a1a1f">
      <div style="font-size:14px;color:#b9f2ff;text-transform:uppercase;letter-spacing:2px">💎 Platinum</div>
      <div style="font-size:42px;font-weight:800;color:#b9f2ff;margin:12px 0">$3,497<span style="font-size:16px;color:#888">/mo</span></div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Everything in Gold</li>
        <li>✅ X/Twitter monitoring</li>
        <li>✅ YouTube comment scanning</li>
        <li>✅ AI-powered intent analysis</li>
        <li>✅ Custom branded materials</li>
        <li>✅ Monthly strategy call</li>
        <li>✅ Dedicated account manager</li>
        <li>✅ API access</li>
        <li>✅ White-label option</li>
      </ul>
      <div style="margin-top:16px;font-size:12px;color:#7ac8db">For top dealers who want every advantage</div>
    </div>
  </div>
  <p style="text-align:center;font-size:13px;color:#888;margin-top:8px">All plans include a $500 one-time setup fee · Annual billing saves 2 months · $1 first-week trial available</p>

  <h2 style="margin-top:40px">Enterprise Licensing — Own It Outright</h2>
  <p style="text-align:center;color:#999;margin-bottom:20px;font-size:14px">Want full ownership instead of a monthly subscription? We'll build it, brand it, deploy it, and hand you the keys.</p>
  <div style="display:flex;gap:24px;flex-wrap:wrap;justify-content:center;margin:20px 0">
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #cd7f32;border-radius:12px;padding:24px;text-align:center;background:#1a1208">
      <div style="font-size:14px;color:#cd7f32;text-transform:uppercase;letter-spacing:2px">🏢 Enterprise</div>
      <div style="font-size:38px;font-weight:800;color:#cd7f32;margin:12px 0">$25,000</div>
      <div style="font-size:13px;color:#888;margin-bottom:12px">One-time payment</div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Full source code ownership</li>
        <li>✅ Branded & configured for your business</li>
        <li>✅ Deployed on your infrastructure</li>
        <li>✅ 90 days tech support</li>
        <li>✅ Team training session</li>
        <li>✅ All current features</li>
        <li>❌ Custom feature development</li>
        <li>❌ Resale rights</li>
      </ul>
    </div>
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #daa520;border-radius:12px;padding:24px;text-align:center;background:#1a1200;position:relative">
      <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#daa520;color:#000;padding:2px 16px;border-radius:20px;font-size:11px;font-weight:700">BEST VALUE</div>
      <div style="font-size:14px;color:#daa520;text-transform:uppercase;letter-spacing:2px">🏢 Enterprise+</div>
      <div style="font-size:38px;font-weight:800;color:#daa520;margin:12px 0">$45,000</div>
      <div style="font-size:13px;color:#888;margin-bottom:12px">One-time payment</div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Everything in Enterprise</li>
        <li>✅ Custom features built to spec</li>
        <li>✅ 12 months tech support</li>
        <li>✅ Priority feature requests</li>
        <li>✅ Quarterly strategy calls</li>
        <li>✅ White-label rights</li>
        <li>❌ Multi-industry resale</li>
      </ul>
    </div>
    <div style="flex:1;min-width:220px;max-width:300px;border:2px solid #e5e4e2;border-radius:12px;padding:24px;text-align:center;background:#141418;position:relative">
      <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:linear-gradient(90deg,#daa520,#e5e4e2,#daa520);color:#000;padding:2px 16px;border-radius:20px;font-size:11px;font-weight:700">UNLIMITED</div>
      <div style="font-size:14px;color:#e5e4e2;text-transform:uppercase;letter-spacing:2px">🏢 Franchise</div>
      <div style="font-size:38px;font-weight:800;color:#e5e4e2;margin:12px 0">$75,000</div>
      <div style="font-size:13px;color:#888;margin-bottom:12px">One-time payment</div>
      <ul style="text-align:left;list-style:none;padding:0;font-size:13px;color:#ccc;line-height:2">
        <li>✅ Everything in Enterprise+</li>
        <li>✅ Resell within ONE licensed industry</li>
        <li>✅ Custom keyword packs per niche</li>
        <li>✅ Lifetime tech support</li>
        <li>✅ Keep 100% of client revenue</li>
        <li>✅ Real estate, auto, watches, crypto</li>
        <li>✅ Unlimited deployments</li>
      </ul>
    </div>
  </div>
  <p style="text-align:center;font-size:13px;color:#888;margin-top:8px">Enterprise licenses include full source code, documentation, and deployment assistance · Payment plans available</p>
  <p style="text-align:center;font-size:12px;color:#666;margin-top:4px">⚖️ All licenses are industry-locked and non-transferable · Unauthorized resale subject to liquidated damages · Full IP retained by licensor</p>

  <h2>Next Steps</h2>
  <div style="background:#1a1200;border:1px solid #b8860b;border-radius:8px;padding:24px;text-align:center">
    <p style="font-size:18px;color:#daa520;font-weight:700;margin-bottom:12px">Ready to turn social media conversations into customers?</p>
    <p style="font-size:14px;color:#ccc;margin-bottom:8px"><strong>Option A:</strong> Start with a subscription — leads flowing within 24 hours</p>
    <p style="font-size:14px;color:#ccc;margin-bottom:8px"><strong>Option B:</strong> Own it outright — full platform, your brand, your data, forever</p>
    <p style="font-size:14px;color:#ccc;margin-bottom:16px">Either way, your first leads are just one call away.</p>
    <p style="font-size:20px;color:#daa520;font-weight:800">📞 Schedule a demo call today</p>
    <p style="font-size:13px;color:#888;margin-top:8px">Contact us to see live results with real data from your market</p>
  </div>
</div>
</body></html>"""


@app.route("/pitch")
def pitch():
    stats = get_analytics_stats()
    score_dist = leads_score_distribution()
    top_subs = leads_by_subreddit()
    subreddit_count = len(get_subreddits())
    max_score_count = max((s["count"] for s in score_dist), default=1)
    return render_template_string(
        PITCH_TEMPLATE,
        company_name=COMPANY_NAME,
        stats=stats,
        score_dist=score_dist,
        top_subs=top_subs,
        subreddit_count=subreddit_count,
        max_score_count=max_score_count,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print(f"🚀 Dashboard running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
