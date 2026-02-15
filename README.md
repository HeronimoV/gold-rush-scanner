# 🚀 Lead Rush

Social media lead generation platform. Monitors Reddit, web forums, and social platforms for buying intent across any industry. Scores leads by intent and provides a web dashboard with lead capture and analytics.

## Setup

```bash
cd gold-rush-scanner
pip install -r requirements.txt
```

No API keys needed for Reddit — uses public JSON endpoints. YouTube scanning requires a free API key (see below).

## Usage

### Run the scanner (one-time)
```bash
python scanner.py
```

### Run in loop mode (every 2 hours)
```bash
python scanner.py --loop
```

### Run with scheduler (uses `schedule` library)
```bash
python run_scheduled.py
```

### Run the dashboard
```bash
python dashboard.py
```
Opens at **http://localhost:5000** — view leads, filter, add notes, export CSV, manage form submissions.

### Landing page
Serve `landing/index.html` or open it directly. Form submissions go to `/api/submit-lead` on the Flask backend and appear in the dashboard under "Form Submissions".

## YouTube Scanner

To enable YouTube comment scanning:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or use existing)
3. Enable **YouTube Data API v3**
4. Create an API key
5. Set `YOUTUBE_API_KEY = "your-key"` in `config.py`

Without an API key, YouTube scanning is skipped automatically.

## Configuration

Edit `config.py` to customize:
- **SUBREDDITS** — which subreddits to monitor
- **KEYWORDS** — keywords and their intent weights (1-10)
- **MIN_SCORE_THRESHOLD** — minimum score to save (default: 4)
- **YOUTUBE_API_KEY** — YouTube Data API v3 key (free)
- **YOUTUBE_SEARCH_QUERIES** — what to search on YouTube
- **SCAN_INTERVAL_HOURS** — loop/scheduler interval (default: 2)

## Scoring

| Score | Meaning | Example |
|-------|---------|---------|
| 8-10 | High intent — actively looking to buy | "Where's the best place to buy gold bars?" |
| 5-7 | Medium intent — considering purchase | "Thinking about investing in gold" |
| 3-4 | Low intent — general discussion | "Gold prices are interesting" |

## Dashboard Features

- **Quick stats**: total leads, leads today, avg score, top source
- **Lead notes**: editable per lead, saved to DB
- **Form submissions tab**: view/manage landing page leads
- **Filtering**: by score, subreddit, date, contacted status
- **CSV export**: filtered exports
- **Mobile responsive**

## Landing Page

Professional lead capture page in `landing/`:
- Gold/black/white design, mobile responsive
- Collects: name, email, phone, interest, budget, referral source
- Submits to `/api/submit-lead` endpoint
- Replace `[Company Name]` with your business name

## Railway Deployment

1. Install the [Railway CLI](https://docs.railway.app/develop/cli) or connect via GitHub
2. Create a new project on [railway.app](https://railway.app)
3. Link this repo:
   ```bash
   railway login
   railway init
   railway up
   ```
4. Set environment variables in the Railway dashboard:
   - `FLASK_ENV` — set to `production` (or `development` for debug)
   - `YOUTUBE_API_KEY` — optional, for YouTube scanning
5. Railway auto-detects the `Procfile`. The **web** service runs gunicorn, the **worker** runs the scheduler.
6. Your dashboard will be live at the Railway-provided URL. The landing page is at `/landing` or `/apply`.

## File Structure

```
├── config.py            # Configuration
├── db.py                # SQLite database layer
├── scanner.py           # Reddit scanner (with --loop flag)
├── youtube_scanner.py   # YouTube comments scanner
├── run_scheduled.py     # Scheduler using schedule library
├── dashboard.py         # Flask web dashboard + API
├── landing/
│   └── index.html       # Lead capture landing page
├── requirements.txt
└── README.md
```
