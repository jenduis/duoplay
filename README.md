# DuoPlay — Nintendo Switch & 3DS Co-Op Finder

**DuoPlay** (`https://duoplay.vercel.app`) is a fast, static website listing **Nintendo Switch, Switch 2, Nintendo 3DS, and Nintendo DS cooperative & multiplayer games**, with a dedicated static page for every title.

Data is gathered from verified community archives and normalized via a reproducible Python pipeline. Gemini is utilized strictly for editorial prose (summaries, co-op mechanics breakdowns, and setup guides)—never for hallucinating factual player counts or hardware support.

---

## Architecture & Layout

```
├── browser-snippets/          DevTools console scrapers (Co-Optimus)
├── scrapers/                  Data normalizers & TitleDB fetchers
│   ├── cooptimus.py           Parses captured Co-Optimus HTML/JSON records
│   ├── switch_titledb.py      Nintendo Switch TitleDB & icon/banner matcher
│   └── ctr_titledb.py         3DS/DS TitleDB & GameTDB box art matcher
├── pipeline/                  Unified Python pipeline & schema
│   ├── schema/game.schema.json Strict JSON schema for DuoPlay games
│   ├── common.py              Title normalizer, slug generator, similarity matching
│   ├── build_db.py            Merges raw data, curated YAMLs, and overrides
│   ├── enrich_with_gemini.py  Gemini-powered editorial summaries & guides
│   ├── validate.py            Strict data quality gate & coverage reporter
│   ├── run_all.sh             End-to-end data build runner
│   └── tests/                 Pytest test suite for pipeline invariants
├── data/
│   ├── raw/                   Raw captures (cooptimus_switch.json, cooptimus_3ds.json)
│   ├── curated/               Curated YAMLs (download_play_3ds.yaml, overrides.yaml)
│   ├── seed/                  Verified legacy seed entries
│   ├── build/                 Intermediate builds & data/build/report.md
│   └── games.json             Final verified production database (2,136+ games)
└── site/                      Static Astro website
    ├── src/content/guides/    Markdown co-op setup guides
    ├── src/pages/             Static routes (catalog, per-game pages, matchmaker, favorites, guides)
    └── src/scripts/           Pure TS filtering & matchmaker logic (tested with Vitest)
```

---

## Data Sources & Licensing

- **Co-Optimus**: Multiplayer feature flags, couch/online player limits, drop-in/out, and campaign indicators.
- **TitleDB & GhostLand NX (NLib)**: Nintendo Switch Title IDs, publisher names, release dates, and icon assets.
- **GameTDB & CTR TitleDB**: Nintendo 3DS & DS product codes, release dates, and high-resolution cover scans.
- **Backloggd**: Used strictly as a curator ranking signal (`curatorPick`), never creating standalone unverified records.

*Disclaimer: Nintendo Switch, Nintendo 3DS, Nintendo DS, and Joy-Con are registered trademarks of Nintendo Co., Ltd. DuoPlay is an independent fan resource and is not affiliated with or endorsed by Nintendo.*

---

## Data Pipeline Workflow

### 1. Capturing Co-Optimus Data (Manual DevTools Step)
Co-Optimus blocks automated bot scrapers via Cloudflare (HTTP 403). Captures are performed safely via DevTools:
1. Open Chrome / Firefox DevTools Console on:
   - Switch: `https://www.co-optimus.com/games.php?system=28`
   - 3DS: `https://www.co-optimus.com/games.php?system=20`
   - DS: `https://www.co-optimus.com/games.php?system=17`
2. Paste the script from `browser-snippets/cooptimus_snippet.js` and press Enter.
3. Move the downloaded JSON files into `data/raw/` (`cooptimus_switch.json`, `cooptimus_3ds.json`).

### 2. Running the Build Pipeline
```bash
# Setup Python virtualenv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run pytest on the pipeline
.venv/bin/pytest pipeline/tests -q

# Run end-to-end data build and validation
bash pipeline/run_all.sh
```

---

## Website Development & Build

```bash
cd site

# Install dependencies
npm install

# Run unit tests (filters, matchmaker)
npx vitest run

# Run local development server
npm run dev
# -> http://localhost:4321

# Typecheck and build static production distribution
npx astro check
npm run build
```

---

## Deployment to Vercel

The site is configured for zero-configuration static deployment to Vercel:
- **Project Root**: `site`
- **Framework Preset**: `Astro`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: `SITE_URL` (default: `https://duoplay.vercel.app`)
