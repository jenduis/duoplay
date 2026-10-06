#!/usr/bin/env python3
"""Enrich DuoPlay database with editorial prose using Gemini API.

Uses Google GenAI SDK (Interactions API / Structured Output) to generate:
- summary (1-2 sentences)
- coopSummary (clear explanation of co-op mechanics)
- setupGuide (Joy-Con/Download Play hardware guidance)
- vibe ("Cozy", "Story", "Chaos", "Puzzle", "Action", "Competitive")
- difficulty ("Very Chill", "Low", "Medium", "Hard")
- audiences (["couples", "friends", "kids", "family", "party"])

Guarantees:
- Never invents player counts or unverified hardware features.
- Caches every game response in data/cache/enrichment/<id>.json.
- If GEMINI_API_KEY is missing, gracefully copies data/build/games.base.json to data/games.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from common import BUILD, CACHE, DATA, CURATED, load_json, load_yaml, save_json

CACHE_DIR = CACHE / "enrichment"


class EditorialOutput(BaseModel):
    summary: str = Field(description="1-2 sentences giving an engaging overview of the game.")
    coopSummary: str = Field(description="Clear explanation of how co-op works based only on verified modes.")
    setupGuide: str = Field(description="Hardware instructions (e.g. Joy-Con splitting, local wireless, or Download Play).")
    vibe: Literal["Cozy", "Story", "Chaos", "Puzzle", "Action", "Competitive"]
    difficulty: Literal["Very Chill", "Low", "Medium", "Hard"]
    audiences: List[Literal["couples", "friends", "kids", "family", "party"]]


def get_fact_hash(game: Dict[str, Any]) -> str:
    facts = {
        "title": game["title"],
        "platforms": game["platforms"],
        "coop": game["coop"],
        "versus": game["versus"],
        "genres": game["genres"],
        "publisher": game.get("publisher"),
    }
    return hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest()[:16]


def enrich_game_with_gemini(client: Any, game: Dict[str, Any]) -> Optional[EditorialOutput]:
    system_prompt = (
        "You are an expert game editorial assistant for DuoPlay, a catalog of Nintendo Switch and 3DS multiplayer games. "
        "Strict rules:\n"
        "1. Write engaging, warm, clear editorial text.\n"
        "2. NEVER invent player counts or hardware features not in the facts.\n"
        "3. Only mention Joy-Con sharing if local couch max is >= 2.\n"
        "4. Only mention Download Play if downloadPlay is true.\n"
        "5. Output valid JSON matching the schema."
    )

    facts = {
        "title": game["title"],
        "platforms": game["platforms"],
        "coop": game["coop"],
        "versus": game["versus"],
        "maxPlayers": game["maxPlayers"],
        "genres": game["genres"],
        "publisher": game.get("publisher"),
        "releaseDate": game.get("releaseDate"),
    }

    user_prompt = f"Provide editorial co-op details for:\n{json.dumps(facts, indent=2)}"

    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            system_instruction=system_prompt,
            input=user_prompt,
            response_format=[
                {
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": EditorialOutput.model_json_schema(),
                }
            ],
        )
        out_text = interaction.output_text
        if out_text:
            data = json.loads(out_text)
            return EditorialOutput.model_validate(data)
    except Exception as e:
        print(f"[!] Gemini API error for {game['id']}: {e}")
    return None


def run_enrichment(limit: Optional[int] = None, only_id: Optional[str] = None):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    in_path = BUILD / "games.base.json"
    out_path = DATA / "games.json"

    if not in_path.exists():
        sys.exit(f"Base games file not found: {in_path}. Run build_db.py first.")

    games = load_json(in_path)
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[!] GEMINI_API_KEY environment variable not set.")
        print(f"[*] Copying {len(games)} base games directly to {out_path} without AI enrichment.")
        save_json(out_path, games)
        return

    from google import genai
    client = genai.Client(api_key=api_key)

    overrides = load_yaml(CURATED / "overrides.yaml") if (CURATED / "overrides.yaml").exists() else {}

    enriched_count = 0
    cached_count = 0

    for i, g in enumerate(games):
        gid = g["id"]
        if only_id and gid != only_id:
            continue
        if limit and enriched_count >= limit:
            break

        cache_file = CACHE_DIR / f"{gid}.json"
        fact_hash = get_fact_hash(g)

        # Check cache
        if cache_file.exists():
            cached_data = load_json(cache_file)
            if cached_data.get("_hash") == fact_hash:
                g["editorial"].update(cached_data["editorial"])
                g["editorial"]["aiGenerated"] = True
                cached_count += 1
                continue

        # Call Gemini
        print(f"[{i+1}/{len(games)}] Generating editorial for '{g['title']}' ({gid})...")
        editorial = enrich_game_with_gemini(client, g)
        if editorial:
            g["editorial"].update(editorial.model_dump())
            g["editorial"]["aiGenerated"] = True
            save_json(cache_file, {
                "_hash": fact_hash,
                "editorial": editorial.model_dump(),
            })
            enriched_count += 1
            time.sleep(0.3)

    # Re-apply overrides to ensure human edits always take precedence
    for g in games:
        gid = g["id"]
        if gid in overrides:
            ov = overrides[gid]
            if "editorial" in ov:
                g["editorial"].update(ov["editorial"])

    save_json(out_path, games)
    print(f"\n[✓] Completed enrichment! (Enriched: {enriched_count}, Cached: {cached_count})")
    print(f"[✓] Saved final dataset to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Enrich games with Gemini API")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of new calls")
    parser.add_argument("--only", type=str, default=None, help="Process single game ID")
    args = parser.parse_args()

    run_enrichment(limit=args.limit, only_id=args.only)


if __name__ == "__main__":
    main()
