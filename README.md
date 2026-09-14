# 📬 Gmail Job Emails to Telegram Bot

Automatically fetch job-related emails from Gmail and send the top 10 to Telegram — 4 times daily.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub     │────▶│   Composio  │────▶│   Python    │────▶│  Telegram   │
│   Actions    │     │   (Gmail)   │     │   Script    │     │   Bot       │
│  (4x/day)   │     │             │     │  (filter)   │     │  (message)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## How It Works

```
Every 4 hours:
  1. GitHub Actions wakes up
  2. Fetches 25 recent emails from Gmail
  3. Filters for job emails (Indeed, Naukri, LinkedIn, etc.)
  4. Ranks them by relevance
  5. Sends top 10 to your Telegram
```

## What You Get in Telegram

```
📬 Top 10 Job Emails
🕐 14 Sep 2026, 12:00 PM
━━━━━━━━━━━━━━━━━━━━━━━━

1. Full Stack Developer – React Node.js @ Scriptweb Solution
├ 👔 Scriptweb Solution
├ 💰 ₹3,00,818.56 a year
├ 📊 3-5 years
├ 📧 Indeed <donotreply@match.indeed.com>
├ 📝 Your background as a Full Stack Developer with...
└ 🔗 Open in Gmail

2. Backend Developer Intern at ChatSpark...
├ 👔 ChatSpark
├ 📧 LinkedIn Jobs
└ 🔗 Open in Gmail

━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sent by gmail-job bot
```

## Project Structure

```
gmail-job-bot/
├── .github/
│   └── workflows/
│       └── daily-jobs.yml    ← GitHub Actions (runs 4x daily)
├── gmail_job.py              ← Main Python script
├── requirements.txt          ← Python dependencies
├── .gitignore               ← Files to ignore in git
└── README.md               ← This file
```

---

## Line-by-Line: GitHub Actions Workflow

This is the file that runs automatically on GitHub's servers. You don't need to install anything — GitHub runs it for you.

### `.github/workflows/daily-jobs.yml` — Complete Breakdown

```yaml
# ─── LINE 1: Name of the workflow ──────────────────────────────────────────────
# This name appears in your GitHub repo under "Actions" tab
# You can name it anything you want
name: Daily Job Emails to Telegram
```

```yaml
# ─── LINE 3-14: When should this run? ─────────────────────────────────────────
# "on" means "trigger when..." 
# "schedule" means "run on a timer" (like an alarm clock)
# "cron" is a special format: minute hour day month day-of-week
#
# Cron format: 'minute hour day month day-of-week'
#   * means "every"
#   '30 2 * * *' = "at minute 30, hour 2, every day, every month, every weekday"
#                    = 2:30 AM UTC every day
#
# IST = Indian Standard Time = UTC + 5:30
# So 2:30 UTC = 8:00 AM IST
on:
  schedule:
    # 8:00 AM IST  = 02:30 UTC  (morning jobs)
    - cron: '30 2 * * *'
    # 12:00 PM IST = 06:30 UTC  (lunch time jobs)
    - cron: '30 6 * * *'
    # 4:00 PM IST  = 10:30 UTC  (afternoon jobs)
    - cron: '30 10 * * *'
    # 8:00 PM IST  = 14:30 UTC  (evening jobs)
    - cron: '30 14 * * *'
```

```yaml
  # ─── LINE 15: Manual trigger ────────────────────────────────────────────────
  # This lets you click "Run workflow" button in GitHub UI
  # Useful for testing without waiting for the schedule
  workflow_dispatch:
```

```yaml
# ─── LINE 17-19: Define the job ───────────────────────────────────────────────
# "jobs" = list of tasks to run
# "fetch-and-send" = name of this job (you can name it anything)
# "runs-on" = what computer to run on
#   ubuntu-latest = free Linux server from GitHub
jobs:
  fetch-and-send:
    runs-on: ubuntu-latest
```

```yaml
    # ─── LINE 21-40: Steps (what to do) ──────────────────────────────────────
    # "steps" = list of actions, run one after another
    steps:

      # STEP 1: Download your code
      # actions/checkout@v4 = GitHub's official action to download repo
      # "v4" = version 4 (latest stable)
      - name: Checkout repository
        uses: actions/checkout@v4

      # STEP 2: Install Python
      # We need Python 3.11 to run our script
      # actions/setup-python@v5 = installs Python on the server
      # cache: 'pip' = saves downloaded packages (faster next time)
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      # STEP 3: Install packages our script needs
      # pip install = Python's package installer
      # requirements.txt = list of packages we need
      - name: Install dependencies
        run: pip install -r requirements.txt

      # STEP 4: Run the actual script
      # "env" = environment variables (secret values)
      # ${{ secrets.XXX }} = reads from GitHub's secret storage
      # These are set in Settings → Secrets → Actions
      - name: Fetch job emails & send to Telegram
        env:
          COMPOSIO_API_KEY: ${{ secrets.COMPOSIO_API_KEY }}
          COMPOSIO_ACCOUNT_ID: ${{ secrets.COMPOSIO_ACCOUNT_ID }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python gmail_job.py
```

---

## Line-by-Line: Python Script

### `gmail_job.py` — Complete Breakdown

```python
# ─── LINE 1-5: File header ────────────────────────────────────────────────────
#!/usr/bin/env python3          # Makes file executable from terminal
"""
gmail-job-bot — Fetch top 10 job emails from Gmail & send to Telegram
"""                              # Docstring = description of what file does
```

```python
# ─── LINE 7-12: Import libraries ──────────────────────────────────────────────
# "import" = load extra tools/functions from other packages
import os       # Access environment variables (secrets)
import sys      # Exit the program early if needed
import json     # Work with JSON data
import re       # Regular expressions (find patterns in text)
import requests # Make HTTP requests (call APIs)
from datetime import datetime, timedelta  # Work with dates/times
```

```python
# ─── LINE 14-18: Read secrets from environment ────────────────────────────────
# os.environ.get("NAME", "") = read env var, default to empty string if missing
# These come from GitHub Secrets or your ~/.zshrc
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "")     # Composio API key
COMPOSIO_ACCOUNT_ID = os.environ.get("COMPOSIO_ACCOUNT_ID", "") # Gmail connection ID
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")  # Telegram bot token
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")      # Your chat ID
```

```python
# ─── LINE 20-31: Keywords and domains to match ────────────────────────────────
# Words that indicate a job email
JOB_KEYWORDS = [
    "hiring", "job", "career", "apply", "position",
    "opportunity", "vacancy", "recruitment", "interview",
    "salary", "full stack", "backend", "frontend", "developer",
    "engineer", "remote", "intern", "fresher", "experienced"
]

# Job portal domains (if email is from these, it's definitely a job email)
JOB_DOMAINS = [
    "indeed", "naukri", "linkedin", "glassdoor", "monster",
    "shine", "foundit", "timesjobs", "freshersworld", "internshala",
    "hirist", "cutshort", "wellfound", "angellist", "dice"
]
```

```python
# ─── LINE 34-63: Fetch emails from Gmail via Composio ─────────────────────────
def fetch_job_emails(max_results=25):
    """Fetch emails using Composio Python SDK"""
    try:
        # Import Composio client (installed via pip)
        from composio_client import Composio

        # Create Composio client with your API key
        client = Composio(api_key=COMPOSIO_API_KEY)

        # Execute Gmail tool to fetch emails
        result = client.tools.execute(
            tool_slug='GMAIL_FETCH_EMAILS',        # Which tool to use
            arguments={
                "max_results": max_results,         # How many emails to fetch
                "user_id": "me",                    # "me" = current user
                "verbose": True,                    # Include full details
                "query": "in:inbox (subject:hiring OR subject:job OR subject:developer OR subject:engineer OR subject:apply OR subject:opportunity) newer_than:2d"
                #    ^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                #    Only inbox  Only emails with job-related subjects         Only last 2 days
            },
            connected_account_id=COMPOSIO_ACCOUNT_ID,  # Which Gmail account
            entity_id="amitkumar.devnode@gmail.com"    # Your email address
        )

        # Extract messages from result
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
```

```python
# ─── LINE 66-80: Filter emails (is this a job email?) ─────────────────────────
def is_job_email(msg):
    sender = (msg.get("sender", "") or "").lower()    # Get sender, lowercase
    subject = (msg.get("subject", "") or "").lower()  # Get subject, lowercase
    body = (msg.get("messageText", "") or "").lower() # Get body, lowercase

    # If sender is from a job portal (Indeed, Naukri, etc.) → definitely job
    for domain in JOB_DOMAINS:
        if domain in sender:
            return True

    # If subject contains job keywords → probably job
    for kw in JOB_KEYWORDS:
        if kw in subject:
            return True

    # If body contains 3+ job keywords → likely job
    kw_count = sum(1 for kw in JOB_KEYWORDS if kw in body)
    return kw_count >= 3
```

```python
# ─── LINE 82-118: Rank emails by relevance ────────────────────────────────────
def rank_job_emails(messages):
    scored = []
    for msg in messages:
        score = 0  # Start with score 0
        sender = (msg.get("sender", "") or "").lower()
        subject = (msg.get("subject", "") or "").lower()
        body = (msg.get("messageText", "") or "").lower()

        # Job portals get high scores
        if "indeed" in sender: score += 5      # Indeed = best
        if "naukri" in sender: score += 5      # Naukri = best
        if "linkedin" in sender: score += 4    # LinkedIn = good
        if "glassdoor" in sender: score += 3   # Glassdoor = ok
        if "wellfound" in sender: score += 3   # Wellfound = ok
        if "cutshort" in sender: score += 3    # Cutshort = ok

        # Keywords in subject = more relevant
        for kw in JOB_KEYWORDS:
            if kw in subject: score += 2       # Subject match = +2
            if kw in body: score += 1          # Body match = +1

        # Unread emails = more important
        labels = msg.get("labelIds", [])
        if "UNREAD" in labels: score += 2

        # Recent emails = more relevant
        ts = msg.get("messageTimestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hours_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
                if hours_ago < 6: score += 3     # Last 6 hours = +3
                elif hours_ago < 12: score += 2  # Last 12 hours = +2
                elif hours_ago < 24: score += 1  # Last 24 hours = +1
            except:
                pass

        scored.append((score, msg))

    # Sort by score (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)
    return [msg for _, msg in scored]  # Return only messages (without scores)
```

```python
# ─── LINE 121-196: Format message for Telegram ────────────────────────────────
def extract_job_details(msg):
    """Extract useful info from email"""
    subject = msg.get("subject", "No Subject")
    sender = msg.get("sender", "Unknown")
    body = msg.get("messageText", "") or msg.get("preview", {}).get("body", "")
    ts = msg.get("messageTimestamp", "")
    msg_id = msg.get("messageId", "")

    # Extract company name from sender
    company = sender.split("<")[0].strip() if "<" in sender else sender
    company = company.replace("Indeed", "").replace("Naukri", "").strip()
    if not company:
        company = sender.split("@")[0].replace(".", " ").title()

    # Find salary (₹ or $ followed by numbers)
    salary = ""
    salary_match = re.search(r'[₹$]\s*[\d,\.]+[\s\-to]+[\d,\.]+', body)
    if salary_match:
        salary = salary_match.group(0)

    # Find location
    location = ""
    loc_match = re.search(r'(?:Location|Place|City)[:\s]+([^\n,]+)', body, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()

    # Find experience (e.g., "3-5 years")
    experience = ""
    exp_match = re.search(r'(\d+[\-–]\d+\s*(?:years?|yrs?))', body, re.IGNORECASE)
    if exp_match:
        experience = exp_match.group(1)

    # Remove "Re:", "Fwd:" from subject
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
    """Create beautiful Telegram message"""
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
```

```python
# ─── LINE 198-236: Send to Telegram ───────────────────────────────────────────
def send_telegram(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram has 4096 character limit, so split if too long
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

    # Send each chunk
    for chunk in chunks:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",  # Bold, links, etc.
            "disable_web_page_preview": True
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()  # Raise error if failed
            print(f"✅ Telegram sent ({len(chunk)} chars)")
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            # Try without Markdown if failed
            payload["parse_mode"] = None
            try:
                resp = requests.post(url, json=payload, timeout=15)
                print(f"✅ Telegram sent (plain text)")
            except:
                print(f"❌ Telegram failed completely")
```

```python
# ─── LINE 238-284: Main function ──────────────────────────────────────────────
def main():
    """Main entry point"""
    print("🚀 gmail-job-bot — Fetching job emails...\n")

    # Check all secrets are present
    missing = []
    if not COMPOSIO_API_KEY: missing.append("COMPOSIO_API_KEY")
    if not COMPOSIO_ACCOUNT_ID: missing.append("COMPOSIO_ACCOUNT_ID")
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID: missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)  # Exit with error

    print("📥 Fetching emails from Gmail...")
    messages = fetch_job_emails(max_results=25)

    if not messages:
        print("❌ No emails found.")
        send_telegram("📬 *Job Email Update*\n\n_No emails found. Check Composio connection._")
        sys.exit(1)

    print(f"📧 Found {len(messages)} total emails")

    # Filter only job emails
    job_emails = [m for m in messages if is_job_email(m)]
    print(f"💼 Filtered to {len(job_emails)} job emails")

    if not job_emails:
        print("⚠️  No job emails found")
        send_telegram("📬 *Job Email Update*\n\n_No new job emails found._")
        sys.exit(0)

    # Rank and get top 10
    ranked = rank_job_emails(job_emails)
    top_10 = ranked[:10]

    print(f"\n🏆 Top {len(top_10)} job emails:")
    for i, job in enumerate(top_10, 1):
        print(f"  {i}. {job.get('subject', 'No Subject')[:60]}")

    print("\n📤 Sending to Telegram...")
    message = format_telegram_message(top_10)
    send_telegram(message)

    print("\n✅ Done!")

# Run main() when script is executed
if __name__ == "__main__":
    main()
```

---

## Setup Guide

### Complete Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SETUP FLOW (What We Did)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Step 1    │───▶│   Step 2    │───▶│   Step 3    │───▶│   Step 4    │   │
│  │  Telegram   │    │  Composio   │    │   GitHub    │    │  GitHub     │   │
│  │  Bot Setup  │    │  API Key    │    │   Secrets   │    │  Actions    │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│       │                  │                  │                  │             │
│       ▼                  ▼                  ▼                  ▼             │
│  Get Bot Token      Get API Key        Add 4 Secrets     Run Workflow       │
│  Get Chat ID        Get Account ID     (via CLI or UI)   (4x daily)        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### Step 1: Create Telegram Bot

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Name: `Gmail Job Bot`
4. Username: `amit1924_job_bot` (or your choice)
5. Copy the **Bot Token**

### Step 2: Get Your Chat ID

1. Open Telegram, search for your bot
2. Send `/start`
3. Run this command:
   ```bash
   curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates" | python3 -m json.tool | grep -A5 '"chat"'
   ```
4. Copy the `id` number (your Chat ID)

### Step 3: Get Composio Credentials

1. Go to [app.composio.dev](https://app.composio.dev)
2. API Keys → Create → Copy key
3. Toolkits → Gmail → Copy Connected Account ID

---

### Step 4: Push to GitHub

#### Option A: From Terminal (What We Did)

```bash
# Go to project folder
cd ~/Desktop/gmail-job-bot

# Initialize git
git init

# Stage all files
git add .

# Commit
git commit -m "Initial commit"

# Create repo on GitHub and push
gh repo create amiitdev/gmail-job-bot --public --description "Fetch job emails from Gmail and send to Telegram"

# Add remote (if not auto-added)
git remote add origin https://github.com/amiitdev/gmail-job-bot.git

# Push
git push -u origin main
```

**What each command does:**

| Command | What It Does |
|---------|--------------|
| `cd ~/Desktop/gmail-job-bot` | Go to project folder |
| `git init` | Start tracking changes (creates `.git/` folder) |
| `git add .` | Stage all files for commit |
| `git commit -m "..."` | Save a snapshot with a message |
| `gh repo create` | Create repo on GitHub via terminal |
| `git remote add origin` | Link local repo to GitHub |
| `git push -u origin main` | Upload code to GitHub |

---

### Step 5: Add GitHub Secrets

Secrets store your API keys safely. GitHub hides them — nobody can see them after saving.

#### Option A: From Terminal (What We Did) ✅ RECOMMENDED

```bash
# Go to project folder
cd ~/Desktop/gmail-job-bot

# Add all 4 secrets at once
gh secret set COMPOSIO_API_KEY --body "ak_itWxsvJnhuXov_Xp7xsr"
gh secret set COMPOSIO_ACCOUNT_ID --body "ca_SaF5isUHhqP7"
gh secret set TELEGRAM_BOT_TOKEN --body "8807057652:AAECM3FnuCEhqL6rnKjirljTFNbGKsRWzK0"
gh secret set TELEGRAM_CHAT_ID --body "839957465"

# Verify secrets were added
gh secret list
```

**What each command does:**

| Command | What It Does |
|---------|--------------|
| `gh secret set NAME --body "VALUE"` | Add/update a secret |
| `gh secret list` | Show all secrets (names only, values hidden) |

**Expected output:**

```
COMPOSIO_ACCOUNT_ID    2026-09-14T09:37:07Z
COMPOSIO_API_KEY       2026-09-14T09:37:06Z
TELEGRAM_BOT_TOKEN     2026-09-14T09:37:08Z
TELEGRAM_CHAT_ID       2026-09-14T09:37:09Z
```

---

#### Option B: From GitHub UI (Manual Way)

```
┌─────────────────────────────────────────────────────────────────┐
│                  ADDING SECRETS VIA UI                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Go to: https://github.com/amiitdev/gmail-job-bot/settings   │
│                                                                 │
│  2. Click "Secrets and variables" (left sidebar)                │
│                                                                 │
│  3. Click "Actions"                                             │
│                                                                 │
│  4. Click "New repository secret"                               │
│                                                                 │
│  5. Fill in:                                                    │
│     ┌─────────────────────────────────────────────┐             │
│     │ Name:    COMPOSIO_API_KEY                   │             │
│     │ Value:   ak_itWxsvJnhuXov_Xp7xsr            │             │
│     └─────────────────────────────────────────────┘             │
│                                                                 │
│  6. Click "Add secret"                                          │
│                                                                 │
│  7. Repeat for all 4 secrets:                                   │
│     - COMPOSIO_API_KEY                                          │
│     - COMPOSIO_ACCOUNT_ID                                       │
│     - TELEGRAM_BOT_TOKEN                                        │
│     - TELEGRAM_CHAT_ID                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step-by-step with screenshots:**

1. **Go to Settings**
   ```
   https://github.com/amiitdev/gmail-job-bot/settings
   ```

2. **Click "Secrets and variables"**
   ```
   Left sidebar → Scroll down → Click "Secrets and variables"
   ```

3. **Click "Actions"**
   ```
   Click the "Actions" tab under Secrets and variables
   ```

4. **Click "New repository secret"**
   ```
   Big green button → "New repository secret"
   ```

5. **Add each secret:**
   ```
   ┌─────────────────────────────────────────────────────────────┐
   │  Name: COMPOSIO_API_KEY                                     │
   │  Value: ak_itWxsvJnhuXov_Xp7xsr                             │
   │                                                             │
   │  [Add secret]                                               │
   └─────────────────────────────────────────────────────────────┘
   
   Repeat for:
   - COMPOSIO_ACCOUNT_ID → ca_SaF5isUHhqP7
   - TELEGRAM_BOT_TOKEN → 8807057652:AAECM3FnuCEhqL6rnKjirljTFNbGKsRWzK0
   - TELEGRAM_CHAT_ID → 839957465
   ```

---

### Step 6: Enable & Run the Workflow

#### Option A: From Terminal (What We Did)

```bash
# Go to project folder
cd ~/Desktop/gmail-job-bot

# Trigger workflow manually
gh workflow run "Daily Job Emails to Telegram"

# Check if it started
gh run list --limit 3

# Watch it run (optional)
gh run watch
```

**What each command does:**

| Command | What It Does |
|---------|--------------|
| `gh workflow run "NAME"` | Trigger workflow manually |
| `gh run list --limit 3` | Show recent workflow runs |
| `gh run watch` | Live watch the current run |

**Expected output:**

```
IN_PROGRESS  Daily Job Emails to Telegram  main  workflow_dispatch  34828954439
```

**Check logs:**

```bash
# View logs of a specific run
gh run view 34828954439 --log | tail -20
```

**Expected log output:**

```
📥 Fetching emails from Gmail...
📧 Found 25 total emails
💼 Filtered to 25 job emails
📤 Sending to Telegram...
✅ Telegram sent (3967 chars)
✅ Done!
```

---

#### Option B: From GitHub UI (Manual Way)

```
┌─────────────────────────────────────────────────────────────────┐
│               TRIGGER WORKFLOW VIA UI                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Go to: https://github.com/amiitdev/gmail-job-bot/actions     │
│                                                                 │
│  2. Click "I understand my workflows, go ahead and enable them" │
│                                                                 │
│  3. Click "Daily Job Emails to Telegram" (left sidebar)         │
│                                                                 │
│  4. Click "Run workflow" (top right)                            │
│                                                                 │
│  5. Select branch: main                                         │
│                                                                 │
│  6. Click "Run workflow" (green button)                         │
│                                                                 │
│  7. Wait ~30 seconds → Check your Telegram!                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step-by-step:**

1. **Go to Actions tab**
   ```
   https://github.com/amiitdev/gmail-job-bot/actions
   ```

2. **Enable workflows**
   ```
   Click: "I understand my workflows, go ahead and enable them"
   ```

3. **Select the workflow**
   ```
   Left sidebar → Click "Daily Job Emails to Telegram"
   ```

4. **Run it**
   ```
   Top right → Click "Run workflow" button
   
   ┌─────────────────────────────────────────────┐
   │  Branch: main                               │
   │                                             │
   │  [Run workflow]  ← Click this green button  │
   └─────────────────────────────────────────────┘
   ```

5. **Watch it run**
   ```
   Click on the running workflow to see live logs
   ```

---

### Comparison: Terminal vs UI

| Task | Terminal (`gh` CLI) | GitHub UI |
|------|---------------------|-----------|
| Create repo | `gh repo create NAME --public` | Click "New" → Fill form |
| Add secrets | `gh secret set NAME --body "VALUE"` | Settings → Secrets → Add |
| Trigger workflow | `gh workflow run "NAME"` | Actions → Run workflow |
| View logs | `gh run view ID --log` | Click on run → Expand logs |
| Check status | `gh run list` | Actions tab → See list |

**Terminal is faster** — 4 commands vs clicking through 10+ pages.

---

### Full Terminal Setup (Copy-Paste)

```bash
# 1. Go to project
cd ~/Desktop/gmail-job-bot

# 2. Push to GitHub
gh repo create amiitdev/gmail-job-bot --public --description "Gmail Job Bot"
git remote add origin https://github.com/amiitdev/gmail-job-bot.git
git push -u origin main

# 3. Add secrets
gh secret set COMPOSIO_API_KEY --body "YOUR_KEY_HERE"
gh secret set COMPOSIO_ACCOUNT_ID --body "YOUR_ACCOUNT_ID_HERE"
gh secret set TELEGRAM_BOT_TOKEN --body "YOUR_BOT_TOKEN_HERE"
gh secret set TELEGRAM_CHAT_ID --body "YOUR_CHAT_ID_HERE"

# 4. Run workflow
gh workflow run "Daily Job Emails to Telegram"

# 5. Check
gh run list --limit 1
```

---

## Schedule

| IST Time | UTC Time | Cron Expression |
|----------|----------|-----------------|
| 8:00 AM | 02:30 | `30 2 * * *` |
| 12:00 PM | 06:30 | `30 6 * * *` |
| 4:00 PM | 10:30 | `30 10 * * *` |
| 8:00 PM | 14:30 | `30 14 * * *` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No emails found" | Check Composio API key and account ID |
| "Telegram error" | Check bot token and chat ID |
| "413 Payload Too Large" | Reduce `max_results` in script |
| Workflow not running | Enable Actions in your repo settings |
| `gh` command not found | Install: `sudo apt install gh` |
| "Repository not found" | Run `gh repo create` first |
| Secrets not working | Verify with `gh secret list` |

---

## Tech Stack

| Tool | Purpose | Free? |
|------|---------|-------|
| [GitHub Actions](https://github.com/features/actions) | Run script 4x daily | ✅ 2000 min/month |
| [Composio](https://composio.dev) | Access Gmail API | ✅ Free tier |
| [Telegram Bot API](https://core.telegram.org/bots/api) | Send messages | ✅ Always free |
| [GitHub CLI (`gh`)](https://cli.github.com/) | Terminal commands | ✅ Always free |
| Python 3.11 | Script language | ✅ Always free |

---

## License

MIT — do whatever you want with it.
