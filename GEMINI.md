# GEMINI.md — Agent Instructions for DuoPlay

DuoPlay is a static site (Astro) listing **Nintendo Switch, Switch 2, 3DS and DS co-op / multiplayer games**,
with one static page per game. Data is built by a Python pipeline from real sources; Gemini writes editorial prose only.

The step-by-step implementation plan lives in the Antigravity artifact `switch_3ds_coop_site_plan.md`.

## Decisions (defaults applied)
- Platforms: `switch`, `switch2` (with `gameShare` flag), `3ds`, `ds` (labelled "DS (plays on 3DS)").
- Brand: **DuoPlay** — "Nintendo Switch & 3DS Co-Op Finder". `SITE_URL` default `https://duoplay.vercel.app`.
- Backloggd list (`data/raw/backloggd_titles.txt`) is only a "Curator's pick" signal; it never adds games by itself.
- Audience: generalized "Player 2" (couples, friends, kids, family, party).

## Standing rules
- Work on branch `feat/switch-3ds-site`; commit after each plan step: `step N: <title>`.
- Use the virtualenv at `.venv`. Never `pip install` globally.
- **Never invent** player counts, platforms, Download Play or GameShare support. Unknown → `null`/`false`,
  and list the game under "needs review" in `data/build/report.md`.
- Field precedence: `overrides.yaml` > curated YAML > Co-Optimus > titledb/3dsdb > NLib > legacy seed > Gemini (editorial only).
- Secrets only via env vars (`GEMINI_API_KEY`). Never commit them.
- Co-Optimus blocks scripted requests (HTTP 403): data is captured manually with `browser-snippets/cooptimus_snippet.js`.

## Layout
```
browser-snippets/   DevTools console capture scripts (Co-Optimus, Backloggd)
scrapers/           cooptimus.py (normalize), switch_titledb.py, ctr_titledb.py
pipeline/           schema/, common.py, build_db.py, enrich_with_gemini.py, validate.py, tests/
data/raw            source captures      data/curated   hand-maintained YAML
data/seed           legacy hand-written entries      data/cache/enrichment   Gemini cache
data/build          intermediate output + report.md  data/games.json         final dataset
site/               Astro project (consumes data/games.json)
```

## Commands
```bash
# Python env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest pipeline/tests -q

# Data refresh (after placing Co-Optimus captures in data/raw/)
bash pipeline/run_all.sh

# Site
cd site && npm install
npm run dev        # http://localhost:4321
npx astro check && npm run build
```
