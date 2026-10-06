#!/usr/bin/env python3
"""Switch Title Database Matcher and Metadata Scraper for DuoPlay.

Downloads community titledb (blawar/titledb US.en.json) and fuzzy-matches against
normalized Co-Optimus Switch games to extract:
- Title ID (16-char hex)
- NSU ID (eShop ID)
- Publisher
- Release date
- Genres
- Icon & Banner URLs
- Official description
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from rapidfuzz import fuzz

# Add project root and pipeline dir
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from common import load_json, normalize_title, save_json

DEFAULT_TITLEDB_URL = "https://raw.githubusercontent.com/blawar/titledb/master/US.en.json"
CACHE_DIR = ROOT / "data" / "raw"


def download_titledb(url: str, dest_path: Path) -> Dict[str, Any]:
    if dest_path.exists() and dest_path.stat().st_size > 100000:
        print(f"[*] Using existing Switch TitleDB at {dest_path}")
        return load_json(dest_path)

    print(f"[*] Downloading Switch TitleDB from {url}...")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    res = requests.get(url, stream=True, timeout=60)
    res.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    print(f"[✓] Downloaded TitleDB ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
    return load_json(dest_path)


def build_titledb_index(raw_db: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build normalized search index of base titles only (ending in 000)."""
    index = []
    for tid, item in raw_db.items():
        if not isinstance(item, dict):
            continue
        # Base games end with 000
        tid_str = str(item.get("id") or tid).upper()
        if not tid_str.endswith("000"):
            continue

        name = item.get("name")
        if not name:
            continue

        norm = normalize_title(name)
        if not norm:
            continue

        index.append({
            "tid": tid_str,
            "name": name,
            "norm": norm,
            "nsuId": str(item.get("nsuId") or "") or None,
            "publisher": item.get("publisher"),
            "releaseDate": str(item.get("releaseDate") or "") or None,
            "genres": item.get("category") if isinstance(item.get("category"), list) else ([item.get("category")] if item.get("category") else []),
            "iconUrl": item.get("iconUrl"),
            "bannerUrl": item.get("bannerUrl"),
            "description": item.get("description"),
            "numberOfPlayers": item.get("numberOfPlayers"),
        })
    return index


def match_titles(
    coop_games: List[Dict[str, Any]],
    titledb_index: List[Dict[str, Any]],
    min_score: float = 90.0
) -> Dict[str, Any]:
    matched = {}
    unmatched = []

    # Map exact normalized names first
    exact_map: Dict[str, List[Dict[str, Any]]] = {}
    for entry in titledb_index:
        exact_map.setdefault(entry["norm"], []).append(entry)

    print(f"[*] Matching {len(coop_games)} Co-Optimus Switch games against {len(titledb_index)} TitleDB base entries...")

    for i, g in enumerate(coop_games):
        title = g["title"]
        norm_title = normalize_title(title)
        best_match = None

        if norm_title in exact_map:
            best_match = exact_map[norm_title][0]
        else:
            # Fuzzy match
            best_score = 0.0
            for entry in titledb_index:
                # Fast token sort ratio
                score = fuzz.token_sort_ratio(norm_title, entry["norm"])
                if score > best_score:
                    best_score = score
                    if score >= min_score:
                        best_match = entry

        if best_match:
            # Fix and enforce HTTPS for icon/banner URLs if HTTP
            icon = best_match.get("iconUrl")
            banner = best_match.get("bannerUrl")
            if icon and icon.startswith("http://"):
                icon = "https://" + icon[7:]
            if banner and banner.startswith("http://"):
                banner = "https://" + banner[7:]

            matched[title] = {
                "title": title,
                "switchTitleId": best_match["tid"],
                "nsuId": best_match["nsuId"],
                "publisher": best_match["publisher"],
                "releaseDate": best_match["releaseDate"],
                "genres": best_match["genres"],
                "iconUrl": icon,
                "bannerUrl": banner,
                "description": best_match["description"],
                "reportedPlayers": best_match["numberOfPlayers"],
            }
        else:
            unmatched.append(title)

    match_rate = len(matched) / len(coop_games) * 100 if coop_games else 0.0
    print(f"[✓] Matched: {len(matched)} / {len(coop_games)} ({match_rate:.1f}%)")
    print(f"    Unmatched: {len(unmatched)}")
    return {
        "matched": matched,
        "unmatched": unmatched,
        "match_rate": match_rate
    }


def main():
    parser = argparse.ArgumentParser(description="Switch TitleDB Scraper & Matcher")
    parser.add_argument("--coop-in", default=ROOT / "data" / "raw" / "cooptimus_switch.norm.json", type=Path)
    parser.add_argument("--titledb-url", default=DEFAULT_TITLEDB_URL)
    parser.add_argument("--titledb-cache", default=ROOT / "data" / "raw" / "titledb_US.en.large.json", type=Path)
    parser.add_argument("--out", default=ROOT / "data" / "raw" / "switch_titledb.json", type=Path)
    args = parser.parse_args()

    if not args.coop_in.exists():
        sys.exit(f"Input file not found: {args.coop_in}")

    coop_games = load_json(args.coop_in)
    raw_titledb = download_titledb(args.titledb_url, args.titledb_cache)
    index = build_titledb_index(raw_titledb)
    result = match_titles(coop_games, index)

    save_json(args.out, result["matched"])
    print(f"[✓] Saved matched records to {args.out}")


if __name__ == "__main__":
    main()
