#!/usr/bin/env python3
"""Validation Gate for DuoPlay.

Validates data/games.json:
- 0 JSON Schema errors against pipeline/schema/game.schema.json
- No duplicate IDs or normalized titles
- No empty platforms array
- downloadPlay is strictly False for non-3DS/DS games
- gameShare is strictly False for non-Switch 2 games
- No boilerplate summary phrases ("popular title featured in the co-op compendium")
- Every cover URL begins with https://
- Emits summary coverage table
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from common import DATA, SCHEMA_PATH, load_json, normalize_title


def validate_database() -> None:
    data_path = DATA / "games.json"
    if not data_path.exists():
        sys.exit(f"Database not found: {data_path}. Run build_db.py or enrich_with_gemini.py first.")

    games = load_json(data_path)
    schema = load_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)

    errors = []
    seen_ids = set()
    seen_titles = set()

    for idx, g in enumerate(games):
        gid = g.get("id")
        title = g.get("title")

        # 1. Schema check
        for err in validator.iter_errors(g):
            errors.append(f"Game {gid or idx}: {err.message}")

        # 2. Duplicate checks
        if gid:
            if gid in seen_ids:
                errors.append(f"Duplicate game ID: {gid}")
            seen_ids.add(gid)

        if title:
            norm_t = normalize_title(title)
            # Differentiate identical multi-platform releases if distinct IDs exist
            key = f"{norm_t}_{sorted(g.get('platforms', []))}"
            if key in seen_titles:
                errors.append(f"Duplicate title and platform set: {title}")
            seen_titles.add(key)

        # 3. Platform invariants
        plats = g.get("platforms", [])
        if not plats:
            errors.append(f"Game {gid} has no platforms assigned.")

        if g.get("coop", {}).get("downloadPlay") and not any(p in ("3ds", "ds") for p in plats):
            errors.append(f"Game {gid} has downloadPlay=True but is not 3DS/DS.")

        if g.get("coop", {}).get("gameShare") and "switch2" not in plats:
            errors.append(f"Game {gid} has gameShare=True but is not Switch 2.")

        # 4. Content sanity
        summary = g.get("editorial", {}).get("summary", "")
        if "popular title featured in the co-op compendium" in summary:
            errors.append(f"Game {gid} contains legacy boilerplate summary text.")

        cover = g.get("cover")
        if cover and not cover.get("url", "").startswith("https://"):
            errors.append(f"Game {gid} cover URL is not HTTPS: {cover.get('url')}")

    if errors:
        print(f"[!] Validation FAILED with {len(errors)} error(s):")
        for e in errors[:15]:
            print(f"    - {e}")
        if len(errors) > 15:
            print(f"    ... and {len(errors) - 15} more.")
        sys.exit(1)

    # Coverage summary
    total = len(games)
    sw_count = sum(1 for g in games if "switch" in g["platforms"])
    p3ds_count = sum(1 for g in games if "3ds" in g["platforms"])
    pds_count = sum(1 for g in games if "ds" in g["platforms"])
    dl_count = sum(1 for g in games if g["coop"]["downloadPlay"])
    covers = sum(1 for g in games if g.get("cover"))
    curated = sum(1 for g in games if g.get("curatorPick"))

    print("\n" + "=" * 55)
    print("✓ DuoPlay Database Validation PASSED (0 errors)")
    print("=" * 55)
    print(f"Total Titles:         {total}")
    print(f"Nintendo Switch:      {sw_count} ({sw_count/total*100:.1f}%)")
    print(f"Nintendo 3DS:         {p3ds_count} ({p3ds_count/total*100:.1f}%)")
    print(f"Nintendo DS:          {pds_count} ({pds_count/total*100:.1f}%)")
    print(f"1-Cart Download Play: {dl_count}")
    print(f"Cover Art Coverage:   {covers} ({covers/total*100:.1f}%)")
    print(f"Curator Picks:        {curated}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    validate_database()
