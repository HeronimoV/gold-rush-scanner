# Railway Setup Instructions

## Current Status
- ❌ **Worker service (scanner) is NOT running** — stopped Feb 16
- ✅ **Web service (dashboard) is running** — gold-rush-scanner-production.up.railway.app
- ❌ **Wrong profile active** — currently `remodeling_colorado`, need `precious_metals`

## What You Need To Do

### 1. Go to Railway Dashboard
https://railway.com/project/4670a3b7-434a-4c34-abff-e1ff413a383c

### 2. Check Services
You should see **TWO services:**
- **web** — Runs the dashboard (gunicorn)
- **worker** — Runs the scanner (run_scheduled.py)

If you only see ONE service, that's the problem. The scanner isn't running.

### 3. Set Environment Variable
Click on **Variables** (or **Settings → Variables**) and add:

```
INDUSTRY_PROFILE=precious_metals
```

This switches from home remodeling leads to gold/silver leads.

### 4. Add Worker Service (If Missing)
If there's no **worker** service:

**Option A: Railway Dashboard**
1. Click "+ New Service"
2. Select "GitHub Repo" → `gold-rush-scanner`
3. Set **Start Command:** `python run_scheduled.py`
4. Deploy

**Option B: Use Procfile (Easier)**
Railway should auto-detect the `Procfile` which has:
```
web: gunicorn dashboard:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300
worker: python run_scheduled.py
```

Make sure **both** are deployed as separate services.

### 5. Restart Everything
1. Click on **web** service → **Redeploy**
2. Click on **worker** service → **Deploy** (or **Redeploy**)

### 6. Check Logs
- **Web logs:** Should show Flask starting, dashboard running
- **Worker logs:** Should show "Starting full scan", "Scanning r/Gold...", etc.

If worker logs show scanning activity, **YOU'RE GOLDEN** 🔥

---

## Expected Output (Worker Logs)
```
📋 Loaded profile: Precious Metals
==================================================
Social Prospector — Starting full scan
Subreddits: 13 | Keywords: 69 | Min score: 4
==================================================
Scanning r/Gold...
  Fetched 50 posts from r/Gold
Lead: u/Legend1191 (score=6) — gold bar, 1 oz gold
Lead: u/Middle_Let1210 (score=6) — buying gold
...
```

---

## Test The Dashboard
1. Open: https://gold-rush-scanner-production.up.railway.app
2. You should see **268 total leads** (or more if scanner is running)
3. Filter by **"precious metals"** keywords
4. Click **"Generate DM"** on a lead → should create personalized outreach message

---

## Demo Checklist (For Tomorrow's Meeting)

✅ **Dashboard live** — Show clean UI with lead stats  
✅ **Fresh gold/silver leads** — Filter to show recent  
✅ **Lead scoring** — Point out high-intent (8-10), medium (5-7), low (1-4)  
✅ **Generate DM** — Click on a first-time buyer, show personalized message  
✅ **Multi-platform** — Mention Reddit, YouTube, web forums, Craigslist, Facebook  
✅ **Multi-industry** — Explain profile system (precious_metals, remodeling_colorado, etc.)  
✅ **Export** — Show CSV export feature  
✅ **Auto-scanning** — Mention worker runs every 2 hours automatically  

---

## If Railway Gives You Issues

**Plan B: Run Locally For Demo**
1. On your laptop:
   ```bash
   cd gold-rush-scanner
   INDUSTRY_PROFILE=precious_metals python scanner.py
   python dashboard.py
   ```
2. Open http://localhost:5000
3. Screen share during demo

Railway should work fine, but local is a backup if something breaks.

---

## Questions?
Ask Kip. I'll help you debug in real-time if needed.

Let's crush this demo tomorrow 🔥
