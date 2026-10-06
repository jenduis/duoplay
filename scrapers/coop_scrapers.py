#!/usr/bin/env python3
"""
Co-Op & Multiplayer Database Scraper Suite
==========================================
A comprehensive, production-ready Python tool to scrape:
1. Co-Optimus (All consoles, couch co-op, split-screen, online co-op, ratings)
2. Unofficial Multiplayer Mods Megalist (Single-player games modded into co-op)
3. Nucleus Co-Op / Splitscreen.me (PC games converted to split-screen)
4. SteamGridDB & Steam Cover Art Downloader (Automated 600x900 vertical box art)

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
    print("Missing required libraries. Run: pip install requests beautifulsoup4")

# Standard headers to mimic modern desktop browsers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# Co-Optimus System IDs
COOPTIMUS_SYSTEMS = {
    "pc": 4,
    "switch": 28,
    "ps5": 30,
    "ps4": 22,
    "ps3": 2,
    "xboxseries": 31,
    "xboxone": 24,
    "xbox360": 1,
    "3ds": 20,
    "ds": 17,
    "wiiu": 21,
    "wii": 9,
}

class CoOptimusScraper:
    """Scrapes game entries, co-op feature flags, and player counts from Co-Optimus."""

    BASE_URL = "https://www.co-optimus.com/games.php"

    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.delay = delay

    def scrape_system(self, system_name: str, couch_only: bool = False, max_pages: int = 50) -> List[Dict[str, Any]]:
        system_id = COOPTIMUS_SYSTEMS.get(system_name.lower())
        if not system_id:
            print(f"[!] Unknown system: '{system_name}'. Choose from: {list(COOPTIMUS_SYSTEMS.keys())}")
            return []

        print(f"\n[*] Scraping Co-Optimus for '{system_name}' (ID: {system_id}) | Couch Only: {couch_only}")
        results = []
        page = 1

        while page <= max_pages:
            params = {
                "system": system_id,
                "sort": "title",
                "direction": "ASC",
                "page": page
            }
            if couch_only:
                params["couch"] = "true"

            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            print(f"  -> Fetching Page {page}: {url}")

            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    print(f"  [!] HTTP {response.status_code} on page {page}. Stopping.")
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                rows = soup.select("table.game-list tbody tr, table.table-striped tbody tr, #game-table tr")
                
                # If table selector fails, try alternative game links
                if not rows:
                    cards = soup.select(".game-entry, .game-item, div[id*='game_']")
                    if not cards and page > 1:
                        print("  [*] No more games found on this page. Finished.")
                        break

                games_on_page = 0
                for row in rows:
                    title_elem = row.select_one("a[href*='/game/']")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    rel_url = title_elem.get("href", "")
                    game_url = urllib.parse.urljoin("https://www.co-optimus.com", rel_url)

                    # Extract columns (Couch co-op, Online, Campaign, etc.)
                    cols = [c.get_text(strip=True) for c in row.find_all("td")]
                    couch_players = cols[1] if len(cols) > 1 else "Unknown"
                    online_players = cols[2] if len(cols) > 2 else "Unknown"
                    rating = cols[4] if len(cols) > 4 else "N/A"

                    results.append({
                        "title": title,
                        "system": system_name.upper(),
                        "couch_players": couch_players,
                        "online_players": online_players,
                        "cooptimus_rating": rating,
                        "cooptimus_url": game_url,
                        "source": "Co-Optimus"
                    })
                    games_on_page += 1

                print(f"     Found {games_on_page} games on page {page}.")
                if games_on_page == 0:
                    break

                page += 1
                time.sleep(self.delay)

            except Exception as e:
                print(f"  [!] Error fetching page {page}: {e}")
                break

        print(f"[+] Total games scraped for {system_name}: {len(results)}")
        return results


class MegalistScraper:
    """Scrapes the Unofficial Multiplayer Mods Mega-List (Megalist)."""

    URL = "https://megalist.neocities.org/mpm"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"\n[*] Scraping Unofficial Multiplayer Mods Mega-List: {self.URL}")
        results = []

        try:
            response = self.session.get(self.URL, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            # Megalist embeds data inside table or pre-rendered lists
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                    links = [a.get("href") for a in row.find_all("a") if a.get("href")]
                    
                    if len(cells) >= 2 and cells[0].lower() != "game":
                        game_name = cells[0]
                        mod_name = cells[1] if len(cells) > 1 else ""
                        details = cells[2] if len(cells) > 2 else ""

                        results.append({
                            "title": game_name,
                            "mod_name": mod_name,
                            "details": details,
                            "links": links,
                            "category": "Unofficial Multiplayer Mod / Source Port",
                            "source": "MPM Megalist"
                        })

            # Check if backend Google Sheets link is embedded in script tags
            scripts = soup.find_all("script")
            for s in scripts:
                if s.string and "spreadsheets/d/" in s.string:
                    sheet_match = re.search(r"spreadsheets/d/([a-zA-Z0-9-_]+)", s.string)
                    if sheet_match:
                        sheet_id = sheet_match.group(1)
                        print(f"  -> Discovered backend Google Sheet ID: {sheet_id}")
                        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
                        sheet_res = self.session.get(sheet_url, timeout=15)
                        if sheet_res.status_code == 200:
                            reader = csv.reader(sheet_res.text.splitlines())
                            header = next(reader, None)
                            for r in reader:
                                if len(r) >= 2 and r[0].strip():
                                    results.append({
                                        "title": r[0].strip(),
                                        "mod_name": r[1].strip() if len(r) > 1 else "",
                                        "details": r[2].strip() if len(r) > 2 else "",
                                        "category": "Unofficial Multiplayer Mod / Source Port",
                                        "source": "MPM Megalist (Direct Sheet)"
                                    })
                            print(f"     Successfully extracted {len(results)} mods directly from Sheet API!")
                            break

        except Exception as e:
            print(f"[!] Error fetching Megalist: {e}")

        print(f"[+] Total unofficial multiplayer mods extracted: {len(results)}")
        return results


class NucleusCoopScraper:
    """Scrapes community split-screen handlers from Splitscreen.me (Nucleus Co-op)."""

    API_URL = "https://hub.splitscreen.me/api/v1/allhandlers"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def scrape(self) -> List[Dict[str, Any]]:
        print(f"\n[*] Scraping Nucleus Co-op (Splitscreen.me) Handlers API: {self.API_URL}")
        results = []
        try:
            res = self.session.get(self.API_URL, timeout=15)
            if res.status_code == 200:
                data = res.json()
                handlers = data if isinstance(data, list) else data.get("handlers", [])
                for h in handlers:
                    title = h.get("gameName") or h.get("name") or h.get("title")
                    if title:
                        results.append({
                            "title": title.strip(),
                            "category": "Nucleus Co-Op Split-Screen Handler",
                            "max_players": h.get("maxPlayers", "2-4 Players"),
                            "handler_id": h.get("_id", ""),
                            "url": f"https://hub.splitscreen.me/handler/{h.get('_id', '')}",
                            "source": "Splitscreen.me"
                        })
                print(f"[+] Total Nucleus Co-op split-screen game handlers scraped: {len(results)}")
            else:
                print(f"[!] Failed to fetch Nucleus handlers (HTTP {res.status_code})")
        except Exception as e:
            print(f"[!] Error fetching Nucleus Co-op: {e}")

        return results


class CoverArtFetcher:
    """Fetches official vertical cover art (600x900) via Steam API or SteamGridDB."""

    STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
    STEAM_CDN_TEMPLATE = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"

    def __init__(self, steamgriddb_api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.api_key = steamgriddb_api_key

    def get_steam_cover(self, game_title: str) -> Optional[str]:
        """Finds vertical library box art using Steam Store search."""
        try:
            params = {"term": game_title, "l": "english", "cc": "US"}
            res = self.session.get(self.STEAM_SEARCH_URL, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                if items:
                    appid = items[0]["id"]
                    cover_url = self.STEAM_CDN_TEMPLATE.format(appid=appid)
                    # Verify image exists
                    check = self.session.head(cover_url, timeout=5)
                    if check.status_code == 200:
                        return cover_url
                    # Fallback to header image
                    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
        except Exception:
            pass
        return None

    def get_steamgriddb_cover(self, game_title: str) -> Optional[str]:
        """Fetches vertical grid from SteamGridDB using API key (if provided)."""
        if not self.api_key:
            return None
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            search_url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(game_title)}"
            res = self.session.get(search_url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("data"):
                    game_id = data["data"][0]["id"]
                    grid_url = f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}?dimensions=600x900"
                    grid_res = self.session.get(grid_url, headers=headers, timeout=10)
                    if grid_res.status_code == 200:
                        grid_data = grid_res.json()
                        if grid_data.get("data"):
                            return grid_data["data"][0]["url"]
        except Exception:
            pass
        return None

    def download_cover(self, game_title: str, output_dir: str = "covers") -> Optional[str]:
        """Downloads vertical box art image to output directory."""
        os.makedirs(output_dir, exist_ok=True)
        filename = re.sub(r'[^a-zA-Z0-9]+', '_', game_title.lower()).strip('_') + ".jpg"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            return filepath

        cover_url = self.get_steamgriddb_cover(game_title) or self.get_steam_cover(game_title)
        if not cover_url:
            return None

        try:
            img_res = self.session.get(cover_url, timeout=15)
            if img_res.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_res.content)
                return filepath
        except Exception:
            pass

        return None


def export_data(data: List[Dict[str, Any]], filename_base: str):
    """Exports dataset to both JSON and CSV formats."""
    json_path = f"{filename_base}.json"
    csv_path = f"{filename_base}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if data:
        keys = list(data[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

    print(f"\n[+] Data successfully exported to:")
    print(f"    - JSON: {os.path.abspath(json_path)}")
    print(f"    - CSV:  {os.path.abspath(csv_path)}")


def main():
    parser = argparse.ArgumentParser(description="Multiplayer & Co-Op Scraper Suite")
    parser.add_argument("--target", choices=["cooptimus", "megalist", "nucleus", "all"], default="all",
                        help="Target source to scrape (default: all)")
    parser.add_argument("--system", default="switch",
                        help=f"System for Co-Optimus (e.g. {', '.join(COOPTIMUS_SYSTEMS.keys())})")
    parser.add_argument("--couch-only", action="store_true",
                        help="Filter Co-Optimus by couch / local co-op only")
    parser.add_argument("--steamgriddb-key", default=None,
                        help="Optional SteamGridDB API key for HD covers")
    parser.add_argument("--download-covers", action="store_true",
                        help="Download box art for extracted games")
    parser.add_argument("--output", default="scraped_coop_database",
                        help="Base output filename (without extension)")

    args = parser.parse_args()
    all_results = []

    # 1. Scrape Co-Optimus
    if args.target in ["cooptimus", "all"]:
        scraper = CoOptimusScraper(delay=1.0)
        coop_games = scraper.scrape_system(args.system, couch_only=args.couch_only)
        all_results.extend(coop_games)

    # 2. Scrape Megalist (Unofficial Mods)
    if args.target in ["megalist", "all"]:
        mega_scraper = MegalistScraper()
        mods = mega_scraper.scrape()
        all_results.extend(mods)

    # 3. Scrape Nucleus Co-Op
    if args.target in ["nucleus", "all"]:
        nucleus_scraper = NucleusCoopScraper()
        nucleus_games = nucleus_scraper.scrape()
        all_results.extend(nucleus_games)

    # 4. Optional Cover Art Fetcher
    if args.download_covers and all_results:
        print(f"\n[*] Downloading cover art for top 25 scraped titles...")
        fetcher = CoverArtFetcher(steamgriddb_api_key=args.steamgriddb_key)
        for g in all_results[:25]:
            title = g.get("title", "")
            path = fetcher.download_cover(title)
            if path:
                print(f"  [✓] Saved cover: {title} -> {path}")
            else:
                print(f"  [-] Cover not found: {title}")

    # Export
    if all_results:
        export_data(all_results, args.output)
    else:
        print("[!] No data was extracted.")


if __name__ == "__main__":
    main()
