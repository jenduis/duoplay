#!/usr/bin/env python3
"""Co-Optimus Scraper & Normalizer for DuoPlay.

Handles:
1. `normalize`: Parses raw DevTools snippet dumps (`cooptimus_<system>.json`)
   into standardized clean records (`cooptimus_<system>.norm.json`).
2. `fetch`: Direct HTTP scraper (Note: Co-Optimus frequently blocks automated requests with HTTP 403,
   so browser-snippets/cooptimus_snippet.js is the primary method).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    pass

COOPTIMUS_SYSTEMS = {
    "switch": 28,
    "3ds": 20,
    "ds": 17,
}


def parse_player_count(text: str) -> Optional[int]:
    """Extract maximum player count integer from string like '2 Players', '4', 'Unknown'."""
    if not text or text.lower() in ("unknown", "n/a", "none", "-"):
        return None
    m = re.findall(r"\b\d+\b", text)
    if m:
        return int(m[-1])  # taking max if range like '2-4'
    return None


def normalize_record(raw: Dict[str, Any], default_system: str = "switch") -> Dict[str, Any]:
    """Normalize a raw Co-Optimus record captured from the browser snippet or fetcher."""
    title = (raw.get("title") or "").strip()
    system = (raw.get("system") or default_system).lower()
    if system in ("28", "switch"):
        platform = "switch"
    elif system in ("20", "3ds"):
        platform = "3ds"
    elif system in ("17", "ds"):
        platform = "ds"
    else:
        platform = system

    url = raw.get("url") or ""
    release_date = raw.get("release_date") or None

    cols = raw.get("columns") or []
    features = [f.lower() for f in raw.get("features") or []]
    details = (raw.get("details") or "").lower()

    # Determine player counts
    # Table column layout when available: [Title, Couch/Local, Online, Date/Rating, ...]
    local_max = None
    online_max = None
    lan_max = None

    if len(cols) >= 3:
        local_max = parse_player_count(cols[1])
        online_max = parse_player_count(cols[2])
    
    # Fallback to parsing details text
    if local_max is None:
        couch_match = re.search(r"couch(?: co-op)?[:\s]*(\d+)", details)
        if couch_match:
            local_max = int(couch_match.group(1))
        elif "couch co-op" in details or "local co-op" in details or "same-screen" in details:
            local_max = 2

    if online_max is None:
        online_match = re.search(r"online(?: co-op)?[:\s]*(\d+)", details)
        if online_match:
            online_max = int(online_match.group(1))

    if lan_max is None:
        lan_match = re.search(r"lan(?: co-op)?[:\s]*(\d+)", details)
        if lan_match:
            lan_max = int(lan_match.group(1))

    # Feature flags
    campaign = False
    if any("campaign" in f for f in features) or "co-op campaign" in details or "campaign co-op" in details:
        campaign = True

    drop_in_out = None
    if any("drop" in f for f in features) or "drop-in/drop-out" in details or "drop in" in details:
        drop_in_out = True

    split_screen = False
    if any("split" in f for f in features) or "split-screen" in details or "split screen" in details:
        split_screen = True

    same_screen = False
    if any("same" in f for f in features) or "same-screen" in details or "shared screen" in details:
        same_screen = True
    elif local_max and local_max > 1 and not split_screen:
        same_screen = True

    return {
        "title": title,
        "platform": platform,
        "local_max": local_max,
        "online_max": online_max,
        "lan_max": lan_max,
        "campaign": campaign,
        "drop_in_out": drop_in_out,
        "split_screen": split_screen,
        "same_screen": same_screen,
        "url": url,
        "release_date": release_date,
    }


def normalize_file(in_path: Path, out_path: Path, default_system: str = "switch") -> None:
    with open(in_path, encoding="utf-8") as f:
        data = json.load(f)

    norm_records = []
    with_players = 0
    for r in data:
        norm = normalize_record(r, default_system=default_system)
        if norm["title"]:
            norm_records.append(norm)
            if norm["local_max"] is not None or norm["online_max"] is not None:
                with_players += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(norm_records, f, indent=2, ensure_ascii=False)

    pct = (with_players / len(norm_records) * 100) if norm_records else 0.0
    print(f"[✓] Normalized {len(norm_records)} games -> {out_path}")
    print(f"    Player count coverage: {with_players}/{len(norm_records)} ({pct:.1f}%)")


def fetch_system(system_name: str, out_path: Path) -> None:
    system_id = COOPTIMUS_SYSTEMS.get(system_name.lower())
    if not system_id:
        sys.exit(f"Unknown system: {system_name}. Available: {list(COOPTIMUS_SYSTEMS.keys())}")

    print(f"[*] Attempting automated scrape for '{system_name}' (ID {system_id})...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    url = f"https://www.co-optimus.com/games.php?system={system_id}"
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 403:
        print("[!] Co-Optimus returned HTTP 403 Forbidden.")
        print("[!] Please run browser-snippets/cooptimus_snippet.js in your browser DevTools Console instead.")
        sys.exit(1)
    elif res.status_code != 200:
        sys.exit(f"[!] HTTP {res.status_code} error from Co-Optimus.")
    print("[+] Page fetched successfully (handling full crawl is advised via browser snippet).")


def main():
    parser = argparse.ArgumentParser(description="Co-Optimus Scraper & Normalizer")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    norm_parser = subparsers.add_parser("normalize", help="Normalize raw browser dump JSON")
    norm_parser.add_argument("--in", dest="in_file", required=True, type=Path, help="Input raw JSON path")
    norm_parser.add_argument("--out", dest="out_file", required=True, type=Path, help="Output normalized JSON path")
    norm_parser.add_argument("--system", default="switch", help="Default system (switch, 3ds, ds)")

    fetch_parser = subparsers.add_parser("fetch", help="Attempt direct fetch (may 403)")
    fetch_parser.add_argument("--system", required=True, choices=list(COOPTIMUS_SYSTEMS.keys()))
    fetch_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.cmd == "normalize":
        normalize_file(args.in_file, args.out_file, default_system=args.system)
    elif args.cmd == "fetch":
        fetch_system(args.system, args.out_path)


if __name__ == "__main__":
    main()
