"""Email and webhook notification system for lead alerts."""

import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL, WEBHOOK_URL,
)

log = logging.getLogger("notifications")


def _smtp_configured():
    return all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL])


def _send_email(subject, html_body):
    """Send an HTML email via SMTP. Fails silently with a log warning."""
    if not _smtp_configured():
        log.info(f"SMTP not configured — skipping email: {subject}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [NOTIFY_EMAIL], msg.as_string())
        log.info(f"Email sent: {subject}")
        return True
    except Exception as e:
        log.warning(f"Failed to send email: {e}")
        return False


def _send_webhook(text):
    """Send a notification to Slack/Discord webhook. Fails silently."""
    if not WEBHOOK_URL:
        return False
    try:
        payload = {"content": text} if "discord" in WEBHOOK_URL.lower() else {"text": text}
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        log.info("Webhook notification sent")
        return True
    except Exception as e:
        log.warning(f"Webhook failed: {e}")
        return False


def notify_high_intent_lead(username, subreddit, score, content, url):
    """Notify when a high-intent lead (score >= 8) is found."""
    subject = f"🔥 High-Intent Lead (Score {score}) — u/{username}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#b8860b">⛏️ Gold Rush Scanner — High-Intent Lead</h2>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="padding:8px;font-weight:bold;color:#666">User</td><td style="padding:8px"><a href="https://reddit.com/u/{username}">u/{username}</a></td></tr>
        <tr style="background:#f9f9f9"><td style="padding:8px;font-weight:bold;color:#666">Score</td><td style="padding:8px"><strong style="color:#2a5">{score}/10</strong></td></tr>
        <tr><td style="padding:8px;font-weight:bold;color:#666">Subreddit</td><td style="padding:8px">r/{subreddit}</td></tr>
        <tr style="background:#f9f9f9"><td style="padding:8px;font-weight:bold;color:#666">Content</td><td style="padding:8px">{content[:500]}</td></tr>
        <tr><td style="padding:8px;font-weight:bold;color:#666">Link</td><td style="padding:8px"><a href="{url}">{url}</a></td></tr>
      </table>
      <p style="margin-top:16px;color:#999;font-size:12px">Sent by Gold Rush Scanner</p>
    </div>
    """
    _send_email(subject, html)
    _send_webhook(f"🔥 High-intent lead (score {score}): u/{username} in r/{subreddit} — {url}")


def notify_form_submission(name, email, phone, interest, budget, referral_source):
    """Notify when a form submission comes in."""
    subject = f"📋 New Form Lead — {name} ({email})"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <h2 style="color:#b8860b">⛏️ Gold Rush Scanner — New Form Submission</h2>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="padding:8px;font-weight:bold;color:#666">Name</td><td style="padding:8px">{name}</td></tr>
        <tr style="background:#f9f9f9"><td style="padding:8px;font-weight:bold;color:#666">Email</td><td style="padding:8px"><a href="mailto:{email}">{email}</a></td></tr>
        <tr><td style="padding:8px;font-weight:bold;color:#666">Phone</td><td style="padding:8px">{phone or '—'}</td></tr>
        <tr style="background:#f9f9f9"><td style="padding:8px;font-weight:bold;color:#666">Interest</td><td style="padding:8px">{interest or '—'}</td></tr>
        <tr><td style="padding:8px;font-weight:bold;color:#666">Budget</td><td style="padding:8px">{budget or '—'}</td></tr>
        <tr style="background:#f9f9f9"><td style="padding:8px;font-weight:bold;color:#666">Source</td><td style="padding:8px">{referral_source or '—'}</td></tr>
      </table>
      <p style="margin-top:16px;color:#999;font-size:12px">Sent by Gold Rush Scanner</p>
    </div>
    """
    _send_email(subject, html)
    _send_webhook(f"📋 New form lead: {name} ({email}) — Interest: {interest}, Budget: {budget}")
