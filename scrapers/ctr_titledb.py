#!/usr/bin/env python3
"""3DS and DS Title Database Matcher and Box Art Resolver for DuoPlay.

Matches Co-Optimus 3DS/DS titles and curated download_play_3ds.yaml against
open 3DS database releases to extract:
- Title ID
- Product Code (CTR-P-XXXX)
- Box Art from GameTDB (https://art.gametdb.com/3ds/box/US/<4-char id>.png)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from common import load_json, load_yaml, normalize_title, save_json

GHOSTLAND_GAMES_URL = "https://raw.githubusercontent.com/ghost-land/3dsdb/main/data/initial_data/games.json"
CACHE_DIR = ROOT / "data" / "raw"


def download_3dsdb(url: str, dest_path: Path) -> List[Dict[str, Any]]:
    if dest_path.exists() and dest_path.stat().st_size > 50000:
        print(f"[*] Using existing 3DS database at {dest_path}")
        return load_json(dest_path)

    print(f"[*] Downloading 3DS database from {url}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    res = requests.get(url, timeout=30)
    res.raise_for_status()

    with open(dest_path, "wb") as f:
        f.write(res.content)
    print(f"[✓] Downloaded 3DS DB ({dest_path.stat().st_size / 1024:.1f} KB)")
    return load_json(dest_path)


def derive_gametdb_cover(product_code: str, platform: str = "3ds") -> Optional[str]:
    """Derive GameTDB 4-character ID from product code deterministically."""
    if not product_code:
        return None
    # product_code format: CTR-P-AMKE or NTR-P-AMKE or similar
    m = re.search(r"-[A-Z0-9]-([A-Z0-9]{4})", product_code.upper())
    if not m:
        m = re.search(r"\b([A-Z0-9]{4})\b", product_code.upper())
    if not m:
        return None

    code4 = m.group(1)
    subpath = "3ds" if platform == "3ds" else "ds"
    # Construct canonical standard GameTDB URL for US/EN cover
    return f"https://art.gametdb.com/{subpath}/box/US/{code4}.png"


def match_titles(
    queries: List[Dict[str, Any]],
    db_items: List[Dict[str, Any]],
    min_score: float = 88.0
) -> Dict[str, Any]:
    matched = {}
    unmatched = []

    # Build normalized lookup index
    exact_map: Dict[str, List[Dict[str, Any]]] = {}
    index = []
    for item in db_items:
        name = item.get("name")
        if not name:
            continue
        p_code = item.get("product_code") or ""
        tid = item.get("tid") or ""
        norm = normalize_title(name)
        entry = {
            "name": name,
            "norm": norm,
            "product_code": p_code,
            "tid": tid,
            "region": item.get("region", "US")
        }
        index.append(entry)
        exact_map.setdefault(norm, []).append(entry)

    print(f"[*] Matching {len(queries)} 3DS/DS titles against {len(index)} database releases...")

    for q in queries:
        title = q["title"]
        norm_title = normalize_title(title)
        platform = q.get("platform", "3ds")

        best_match = None
        if norm_title in exact_map:
            best_match = exact_map[norm_title][0]
        else:
            best_score = 0.0
            for entry in index:
                score = fuzz.token_sort_ratio(norm_title, entry["norm"])
                if score > best_score:
                    best_score = score
                    if score >= min_score:
                        best_match = entry

        if best_match:
            pcode = best_match["product_code"]
            cover_url = derive_gametdb_cover(pcode, platform=platform)

            matched[title] = {
                "title": title,
                "platform": platform,
                "ctrProductCode": pcode or None,
                "tid": best_match["tid"] or None,
                "coverUrl": cover_url,
                "coverSource": "gametdb" if cover_url else None
            }
        else:
            unmatched.append(title)

    match_rate = len(matched) / len(queries) * 100 if queries else 0.0
    print(f"[✓] 3DS matched: {len(matched)} / {len(queries)} ({match_rate:.1f}%)")
    return {"matched": matched, "unmatched": unmatched}


def main():
    parser = argparse.ArgumentParser(description="3DS & DS TitleDB Scraper")
    parser.add_argument("--coop-in", default=ROOT / "data" / "raw" / "cooptimus_3ds.norm.json", type=Path)
    parser.add_argument("--curated-in", default=ROOT / "data" / "curated" / "download_play_3ds.yaml", type=Path)
    parser.add_argument("--db-cache", default=ROOT / "data" / "raw" / "3dsdb.large.json", type=Path)
    parser.add_argument("--out", default=ROOT / "data" / "raw" / "3ds_titledb.json", type=Path)
    args = parser.parse_args()

    queries = []
    seen = set()

    if args.coop_in.exists():
        for g in load_json(args.coop_in):
            t = g["title"]
            if t.lower() not in seen:
                seen.add(t.lower())
                queries.append({"title": t, "platform": g.get("platform", "3ds")})

    if args.curated_in.exists():
        for g in load_yaml(args.curated_in):
            t = g["title"]
            if t.lower() not in seen:
                seen.add(t.lower())
                queries.append({"title": t, "platform": g.get("platform", "3ds")})

    db_items = download_3dsdb(GHOSTLAND_GAMES_URL, args.db_cache)
    res = match_titles(queries, db_items)
    save_json(args.out, res["matched"])
    print(f"[✓] Saved 3DS metadata to {args.out}")


if __name__ == "__main__":
    main()
