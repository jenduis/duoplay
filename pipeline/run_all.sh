#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=== 1. Normalizing raw Co-Optimus data ==="
.venv/bin/python scrapers/cooptimus.py normalize --in data/raw/cooptimus_switch.json --out data/raw/cooptimus_switch.norm.json --system switch
.venv/bin/python scrapers/cooptimus.py normalize --in data/raw/cooptimus_3ds.json --out data/raw/cooptimus_3ds.norm.json --system 3ds

echo "=== 2. Matching Switch TitleDB ==="
.venv/bin/python scrapers/switch_titledb.py

echo "=== 3. Matching 3DS/DS TitleDB & Covers ==="
.venv/bin/python scrapers/ctr_titledb.py

echo "=== 4. Compiling Base Database ==="
.venv/bin/python pipeline/build_db.py

echo "=== 5. Running Gemini Enrichment / Fallback ==="
.venv/bin/python pipeline/enrich_with_gemini.py

echo "=== 6. Validating Final Dataset ==="
.venv/bin/python pipeline/validate.py

echo "=== 7. Running Pytest Suite ==="
.venv/bin/pytest pipeline/tests -q

echo "=== All Pipeline Steps Passed Successfully! ==="
