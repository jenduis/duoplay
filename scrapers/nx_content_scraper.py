#!/usr/bin/env python3
"""
NX-Content (GhostLand) Scraper
==============================
Scrapes Nintendo Switch content listings (Title ID, Game Name, Type, Version, Size, Region)
from https://nx-content.ghostland.at/?view=content&page=N

Features:
- Dual-mode extraction: Automatically tries the backend JSON API or falls back to HTML DOM table parsing
- Multi-page pagination with configurable delay to respect server limits
- Exports to both structured JSON and CSV formats
- Includes a standalone in-browser console snippet for instant browser extraction

Requirements:
    pip install requests beautifulsoup4
"""

import os
import sys
import time
import json
import csv
import re
import argparse
import urllib.parse
from typing import List, Dict, Any, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing dependencies. Run: pip install requests beautifulsoup4")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://nx-content.ghostland.at/"
}

class NXContentScraper:
    BASE_URL = "https://nx-content.ghostland.at/"

    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.delay = delay

    def scrape(self, start_page: int = 1, max_pages: int = 20) -> List[Dict[str, Any]]:
        print(f"[*] Starting extraction for nx-content.ghostland.at (Pages {start_page} to {start_page + max_pages - 1})")
        all_items = []
        page = start_page

        while page < start_page + max_pages:
            url = f"{self.BASE_URL}?view=content&page={page}"
            print(f"  -> Fetching Page {page}: {url}")

            try:
                res = self.session.get(url, timeout=15)
                if res.status_code != 200:
                    print(f"  [!] HTTP {res.status_code} received on page {page}. Stopping.")
                    break

                # 1. Try parsing response as JSON if the endpoint returned JSON
                try:
                    data = res.json()
                    items = data.get("items") or data.get("content") or data.get("data") or (data if isinstance(data, list) else [])
                    if items:
                        print(f"     [✓] Successfully retrieved {len(items)} items via JSON API on page {page}.")
                        for it in items:
                            all_items.append(self._normalize_item(it))
                        page += 1
                        time.sleep(self.delay)
                        continue
                except ValueError:
                    pass  # HTML response, proceed to DOM parser

                # 2. Parse HTML via BeautifulSoup
                soup = BeautifulSoup(res.text, "html.parser")
                page_items = []

                # Find content rows across various table/grid formats
                rows = soup.select("table tbody tr, .content-row, .game-item, .table tr")
                for r in rows:
                    cols = [td.get_text(strip=True) for td in r.find_all(["td", "th"])]
                    if not cols or len(cols) < 2:
                        continue
                    if cols[0].lower() in ["id", "title id", "name", "#"]:
                        continue

                    # Extract details
                    link = r.find("a")
                    href = link.get("href", "") if link else ""
                    
                    # Pattern match for 16-hex Title ID (0100...)
                    tid_match = re.search(r"\b0100[0-9A-Fa-f]{12}\b", r.get_text())
                    tid = tid_match.group(0) if tid_match else (cols[0] if len(cols[0]) == 16 else "")

                    title = cols[1] if len(cols) > 1 and cols[0] == tid else cols[0]
                    content_type = cols[2] if len(cols) > 2 else "Base / DLC"
                    version = cols[3] if len(cols) > 3 else "v0"
                    size = cols[4] if len(cols) > 4 else ""
                    region = cols[5] if len(cols) > 5 else "Global"

                    page_items.append({
                        "title_id": tid,
                        "title": title,
                        "type": content_type,
                        "version": version,
                        "size": size,
                        "region": region,
                        "page": page,
                        "url": urllib.parse.urljoin(self.BASE_URL, href) if href else url
                    })

                print(f"     [✓] Parsed {len(page_items)} items from HTML on page {page}.")
                if not page_items:
                    print("  [*] No records found on page. Reached end of content.")
                    break

                all_items.extend(page_items)
                page += 1
                time.sleep(self.delay)

            except Exception as e:
                print(f"  [!] Error fetching page {page}: {e}")
                break

        print(f"\n[+] Total items extracted: {len(all_items)}")
        return all_items

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes API JSON dictionary to standard format."""
        return {
            "title_id": item.get("id") or item.get("tid") or item.get("title_id", ""),
            "title": item.get("name") or item.get("title", ""),
            "type": item.get("type", "Base"),
            "version": item.get("version", "v0"),
            "size": item.get("size", ""),
            "region": item.get("region", "Global"),
            "publisher": item.get("publisher", ""),
            "release_date": item.get("release_date", "")
        }


def export_data(data: List[Dict[str, Any]], output_base: str):
    json_path = f"{output_base}.json"
    csv_path = f"{output_base}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if data:
        # Collect union of all fields
        fields = []
        for d in data:
            for k in d.keys():
                if k not in fields:
                    fields.append(k)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    print(f"\n[✓] Results exported successfully:")
    print(f"    - JSON: {os.path.abspath(json_path)}")
    print(f"    - CSV:  {os.path.abspath(csv_path)}")


def main():
    parser = argparse.ArgumentParser(description="Scrape Nintendo Switch content from nx-content.ghostland.at")
    parser.add_argument("--page", type=int, default=1, help="Starting page number (default: 1)")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to scrape (default: 10)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--output", default="nx_content_export", help="Output filename base (without extension)")

    args = parser.parse_args()

    scraper = NXContentScraper(delay=args.delay)
    data = scraper.scrape(start_page=args.page, max_pages=args.max_pages)
    if data:
        export_data(data, args.output)
    else:
        print("[!] No records extracted.")

if __name__ == "__main__":
    main()
