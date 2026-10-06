import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Locate games.json
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAMES_PATH = os.path.join(ROOT_DIR, "data", "games.json")

GAMES_DATA = []
if os.path.exists(GAMES_PATH):
    try:
        with open(GAMES_PATH, "r", encoding="utf-8") as f:
            GAMES_DATA = json.load(f)
    except Exception as e:
        print(f"Error loading {GAMES_PATH}: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Health check
        if path == "/api" or path == "/api/" or path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {"status": "ok", "service": "api", "games_count": len(GAMES_DATA)}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # Games list / search
        if path == "/api/games":
            search_query = query.get("q", [""])[0].lower().strip()
            platform = query.get("platform", [""])[0].lower().strip()
            dl_play = query.get("download_play", [""])[0].lower() == "true"
            limit = int(query.get("limit", [50])[0])

            results = GAMES_DATA
            if platform:
                results = [g for g in results if platform in g.get("platforms", [])]
            if dl_play:
                results = [g for g in results if g.get("coop", {}).get("downloadPlay", False)]
            if search_query:
                results = [g for g in results if search_query in g.get("title", "").lower()]

            results = results[:limit]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"total": len(results), "games": results}).encode("utf-8"))
            return

        # Single game by ID
        if path.startswith("/api/games/"):
            game_id = path.replace("/api/games/", "").strip("/")
            game = next((g for g in GAMES_DATA if g.get("id") == game_id), None)
            if game:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(game).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Game not found"}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
