#!/usr/bin/env python3
"""
gmail-job-bot — Fetch top 10 job emails from Gmail & send to Telegram
For GitHub Actions: uses Composio API directly
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────────────────────────
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")
COMPOSIO_ACCOUNT_ID = os.environ.get("COMPOSIO_ACCOUNT_ID", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

JOB_KEYWORDS = [
    "hiring", "job", "career", "apply", "position",
    "opportunity", "vacancy", "recruitment", "interview",
    "salary", "full stack", "backend", "frontend", "developer",
    "engineer", "remote", "intern", "fresher", "experienced"
]

JOB_DOMAINS = [
    "indeed", "naukri", "linkedin", "glassdoor", "monster",
    "shine", "foundit", "timesjobs", "freshersworld", "internshala",
    "hirist", "cutshort", "wellfound", "angellist", "dice"
]

# ─── COMPOSIO GMAIL ───────────────────────────────────────────────────────────
def fetch_job_emails(max_results=25):
    """Fetch emails using Composio Python SDK"""
    try:
        from composio_client import Composio

        client = Composio(api_key=COMPOSIO_API_KEY)

        result = client.tools.execute(
            tool_slug='GMAIL_FETCH_EMAILS',
            arguments={
                "max_results": max_results,
                "user_id": "me",
                "verbose": True,
                "query": "in:inbox (subject:hiring OR subject:job OR subject:developer OR subject:engineer OR subject:apply OR subject:opportunity) newer_than:2d"
            },
            connected_account_id=COMPOSIO_ACCOUNT_ID,
            entity_id="amitkumar.devnode@gmail.com"
        )

        if result and result.data:
            messages = result.data.get("messages", [])
            return messages
        return []

    except ImportError:
        print("❌ Composio SDK not installed. Run: pip install composio-client")
        return []
    except Exception as e:
        print(f"❌ Composio SDK error: {e}")
        return []

# ─── FILTER & RANK ────────────────────────────────────────────────────────────
def is_job_email(msg):
    sender = (msg.get("sender", "") or "").lower()
    subject = (msg.get("subject", "") or "").lower()
    body = (msg.get("messageText", "") or "").lower()

    for domain in JOB_DOMAINS:
        if domain in sender:
            return True

    for kw in JOB_KEYWORDS:
        if kw in subject:
            return True

    kw_count = sum(1 for kw in JOB_KEYWORDS if kw in body)
    return kw_count >= 3

def rank_job_emails(messages):
    scored = []
    for msg in messages:
        score = 0
        sender = (msg.get("sender", "") or "").lower()
        subject = (msg.get("subject", "") or "").lower()
        body = (msg.get("messageText", "") or "").lower()

        if "indeed" in sender: score += 5
        if "naukri" in sender: score += 5
        if "linkedin" in sender: score += 4
        if "glassdoor" in sender: score += 3
        if "wellfound" in sender: score += 3
        if "cutshort" in sender: score += 3

        for kw in JOB_KEYWORDS:
            if kw in subject: score += 2
            if kw in body: score += 1

        labels = msg.get("labelIds", [])
        if "UNREAD" in labels: score += 2

        ts = msg.get("messageTimestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hours_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
                if hours_ago < 6: score += 3
                elif hours_ago < 12: score += 2
                elif hours_ago < 24: score += 1
            except:
                pass

        scored.append((score, msg))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [msg for _, msg in scored]

# ─── FORMAT TELEGRAM MESSAGE ──────────────────────────────────────────────────
def extract_job_details(msg):
    subject = msg.get("subject", "No Subject")
    sender = msg.get("sender", "Unknown")
    body = msg.get("messageText", "") or msg.get("preview", {}).get("body", "")
    ts = msg.get("messageTimestamp", "")
    msg_id = msg.get("messageId", "")

    company = sender.split("<")[0].strip() if "<" in sender else sender
    company = company.replace("Indeed", "").replace("Naukri", "").strip()
    if not company:
        company = sender.split("@")[0].replace(".", " ").title()

    salary = ""
    salary_match = re.search(r'[₹$]\s*[\d,\.]+[\s\-to]+[\d,\.]+', body)
    if salary_match:
        salary = salary_match.group(0)

    location = ""
    loc_match = re.search(r'(?:Location|Place|City)[:\s]+([^\n,]+)', body, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()

    experience = ""
    exp_match = re.search(r'(\d+[\-–]\d+\s*(?:years?|yrs?))', body, re.IGNORECASE)
    if exp_match:
        experience = exp_match.group(1)

    clean_subject = re.sub(r'^(Re|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE).strip()

    return {
        "subject": clean_subject,
        "company": company,
        "sender": sender,
        "salary": salary,
        "location": location,
        "experience": experience,
        "body_preview": body[:200].strip(),
        "msg_id": msg_id,
        "timestamp": ts
    }

def format_telegram_message(jobs):
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    header = f"""📬 *Top {len(jobs)} Job Emails*
🕐 {now}
━━━━━━━━━━━━━━━━━━━━━━━━

"""
    job_blocks = []
    for i, job in enumerate(jobs, 1):
        details = extract_job_details(job)
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{details['msg_id']}"

        block = f"""*{i}. {details['subject']}*
├ 👔 {details['company']}"""

        if details['salary']:
            block += f"\n├ 💰 {details['salary']}"
        if details['location']:
            block += f"\n├ 📍 {details['location']}"
        if details['experience']:
            block += f"\n├ 📊 {details['experience']}"

        block += f"\n├ 📧 {details['sender'][:40]}"
        block += f"\n├ 📝 {details['body_preview'][:80]}..."
        block += f"\n└ 🔗 [Open in Gmail]({gmail_link})"
        block += "\n"

        job_blocks.append(block)

    footer = f"""━━━━━━━━━━━━━━━━━━━━━━━━
🤖 _Sent by gmail-job bot_
📊 _Showing top {len(jobs)} by relevance_"""

    return header + "\n".join(job_blocks) + footer

# ─── TELEGRAM ─────────────────────────────────────────────────────────────────
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    chunks = []
    if len(message) > 4000:
        lines = message.split("\n")
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) > 4000:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)
    else:
        chunks = [message]

    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            print(f"✅ Telegram sent ({len(chunk)} chars)")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            payload["parse_mode"] = None
            try:
                resp = requests.post(url, json=payload, timeout=15)
                print(f"✅ Telegram sent (plain text)")
            except:
                print(f"❌ Telegram failed completely")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("🚀 gmail-job-bot — Fetching job emails...\n")

    missing = []
    if not COMPOSIO_API_KEY: missing.append("COMPOSIO_API_KEY")
    if not COMPOSIO_ACCOUNT_ID: missing.append("COMPOSIO_ACCOUNT_ID")
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID: missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    print("📥 Fetching emails from Gmail...")
    messages = fetch_job_emails(max_results=25)

    if not messages:
        print("❌ No emails found.")
        send_telegram("📬 *Job Email Update*\n\n_No emails found. Check Composio connection._")
        sys.exit(1)

    print(f"📧 Found {len(messages)} total emails")

    job_emails = [m for m in messages if is_job_email(m)]
    print(f"💼 Filtered to {len(job_emails)} job emails")

    if not job_emails:
        print("⚠️  No job emails found")
        send_telegram("📬 *Job Email Update*\n\n_No new job emails found._")
        sys.exit(0)

    ranked = rank_job_emails(job_emails)
    top_10 = ranked[:10]

    print(f"\n🏆 Top {len(top_10)} job emails:")
    for i, job in enumerate(top_10, 1):
        print(f"  {i}. {job.get('subject', 'No Subject')[:60]}")

    print("\n📤 Sending to Telegram...")
    message = format_telegram_message(top_10)
    send_telegram(message)

    print("\n✅ Done!")

if __name__ == "__main__":
    main()
