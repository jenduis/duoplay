# DuoPlay & Multiplayer Scrapers - Claude Code Workspace

This workspace contains all assets, scrapers, datasets, and the web application built during the session.

## Directory Structure

```
├── CLAUDE.md                        # Quick instructions and commands for Claude Code
├── README.md                        # General project documentation
├── duoplay-app/                     # Complete web application (Vercel-ready)
│   ├── index.html                   # Inclusive, multi-console responsive interface
│   ├── styles.css                   # Modern dark neon theme & card layouts
│   ├── app.js                       # Client-side multi-filtering, search, & pagination
│   ├── data.js                      # JavaScript database (2,269 games)
│   ├── games.json                   # Raw JSON database (2,269 games)
│   ├── package.json                 # Node metadata
│   ├── vercel.json                  # Vercel deployment config (outputDirectory: .)
│   └── public/                      # Mirrored static assets for Vercel
├── scrapers/                        # Python CLI scraping tools
│   ├── coop_scrapers.py             # Scraper for Co-Optimus, Megalist, Nucleus & covers
│   ├── nx_content_scraper.py        # Scraper for GhostLand / NLib API
│   └── requirements.txt             # Python dependencies (requests, beautifulsoup4)
├── browser-snippets/                # Browser DevTools console scrapers (F12)
│   ├── backloggd_scraper.js         # Scrapes all 24 pages of Backloggd lists
│   ├── cooptimus_setpage_scraper.js # Scrapes all 84 pages of Co-Optimus via native setPage()
│   ├── ghostland_nx_scraper.js      # Extracts Switch Title IDs & player counts from NLib API
│   └── megalist_scraper.js          # Scrapes Unofficial Multiplayer Mods Mega-List
├── datasets/                        # Source datasets
│   ├── all_backloggd_titles.txt     # All 2,269 raw unique titles from the 24-page list
│   └── games_master_2269.json       # Master enriched catalog with platforms & co-op relation
└── pipeline/                        # Generation scripts
    └── build_complete_2269_db.py    # Pipeline to rebuild and enrich games database
```

## Quick Commands for Claude Code

### 1. Launch Web Application Locally
```bash
cd duoplay-app
python3 -m http.server 3000
# Open http://localhost:3000 in your browser
```

### 2. Deploy Web App to Vercel
```bash
cd duoplay-app
npx vercel
# Follow prompt defaults; zero config needed.
```

### 3. Run Python Scrapers
```bash
cd scrapers
pip install -r requirements.txt

# Scrape Co-Optimus Switch couch co-op:
python coop_scrapers.py --target cooptimus --system switch --couch-only

# Scrape Unofficial Multiplayer Mods Megalist:
python coop_scrapers.py --target megalist

# Scrape Nucleus Co-Op split-screen handlers:
python coop_scrapers.py --target nucleus

# Scrape GhostLand NX content:
python nx_content_scraper.py --page 1 --max-pages 10
```

### 4. Rebuild Database After Scraping
```bash
python pipeline/build_complete_2269_db.py
```
