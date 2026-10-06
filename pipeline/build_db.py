#!/usr/bin/env python3
"""Build Unified Database for DuoPlay.

Merges:
1. cooptimus_switch.norm.json, cooptimus_3ds.norm.json
2. switch_titledb.json, 3ds_titledb.json
3. download_play_3ds.yaml
4. legacy_curated.json (96 verified titles)
5. backloggd_titles.txt (curator picks)
6. overrides.yaml (human overrides)

Validates every record against pipeline/schema/game.schema.json,
writes data/build/games.base.json, and generates data/build/report.md.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import jsonschema
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from common import (
    BUILD,
    CURATED,
    DATA,
    RAW,
    SCHEMA_PATH,
    SEED,
    load_json,
    load_yaml,
    normalize_title,
    save_json,
    slugify,
)


def load_backloggd_titles(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {normalize_title(line.strip()) for line in f if line.strip()}


def build_unified_database() -> Dict[str, Any]:
    print("[*] Starting DuoPlay database compilation...")

    # Load sources
    coop_switch = load_json(RAW / "cooptimus_switch.norm.json") if (RAW / "cooptimus_switch.norm.json").exists() else []
    coop_3ds = load_json(RAW / "cooptimus_3ds.norm.json") if (RAW / "cooptimus_3ds.norm.json").exists() else []
    switch_meta = load_json(RAW / "switch_titledb.json") if (RAW / "switch_titledb.json").exists() else {}
    ctr_meta = load_json(RAW / "3ds_titledb.json") if (RAW / "3ds_titledb.json").exists() else {}
    dl_play_yaml = load_yaml(CURATED / "download_play_3ds.yaml") if (CURATED / "download_play_3ds.yaml").exists() else []
    legacy_curated = load_json(SEED / "legacy_curated.json") if (SEED / "legacy_curated.json").exists() else []
    backloggd_picks = load_backloggd_titles(RAW / "backloggd_titles.txt")
    overrides = load_yaml(CURATED / "overrides.yaml") if (CURATED / "overrides.yaml").exists() else {}

    print(f"    - Co-Optimus Switch: {len(coop_switch)}")
    print(f"    - Co-Optimus 3DS: {len(coop_3ds)}")
    print(f"    - Download Play curated: {len(dl_play_yaml)}")
    print(f"    - Legacy curated seed: {len(legacy_curated)}")
    print(f"    - Backloggd pick titles: {len(backloggd_picks)}")

    # Index legacy curated by normalized title
    legacy_map = {normalize_title(item["title"]): item for item in legacy_curated}
    # Index download play curated by normalized title
    dl_play_map = {normalize_title(item["title"]): item for item in dl_play_yaml}

    # Grouping dictionary keyed by normalized title
    games_by_norm: Dict[str, Dict[str, Any]] = {}

    def get_or_create_game(title: str, platform: str) -> Dict[str, Any]:
        norm = normalize_title(title)
        if norm not in games_by_norm:
            games_by_norm[norm] = {
                "title": title,
                "norm": norm,
                "platforms": set(),
                "coop": {
                    "campaign": False,
                    "local": {"max": None, "sameScreen": False, "splitScreen": False},
                    "localWireless": {"max": None},
                    "online": {"max": None},
                    "downloadPlay": False,
                    "gameShare": False,
                    "dropInOut": None,
                },
                "versus": False,
                "maxPlayers": None,
                "genres": [],
                "releaseDate": None,
                "publisher": None,
                "ids": {},
                "cover": None,
                "curatorPick": False,
                "editorial": {
                    "summary": f"{title} offers engaging cooperative play on Nintendo systems.",
                    "coopSummary": "Multiplayer functionality available across supported Nintendo hardware.",
                    "setupGuide": "Refer to in-game multiplayer options or controller settings to configure co-op.",
                    "vibe": "Action",
                    "difficulty": "Medium",
                    "audiences": ["friends"],
                    "aiGenerated": False,
                    "reviewed": False,
                },
                "sources": [],
            }
        g = games_by_norm[norm]
        g["platforms"].add(platform)
        return g

    # 1. Ingest Co-Optimus Switch
    for c in coop_switch:
        g = get_or_create_game(c["title"], "switch")
        g["sources"].append("cooptimus:switch")
        if c.get("url"):
            g["ids"]["cooptimusUrl"] = c["url"]

        if c.get("local_max"):
            cur = g["coop"]["local"]["max"] or 0
            g["coop"]["local"]["max"] = max(cur, c["local_max"])
            if c.get("same_screen"):
                g["coop"]["local"]["sameScreen"] = True
            if c.get("split_screen"):
                g["coop"]["local"]["splitScreen"] = True

        if c.get("online_max"):
            cur = g["coop"]["online"]["max"] or 0
            g["coop"]["online"]["max"] = max(cur, c["online_max"])

        if c.get("lan_max"):
            cur = g["coop"]["localWireless"]["max"] or 0
            g["coop"]["localWireless"]["max"] = max(cur, c["lan_max"])

        if c.get("campaign"):
            g["coop"]["campaign"] = True
        if c.get("drop_in_out") is not None:
            g["coop"]["dropInOut"] = c["drop_in_out"]
        if c.get("release_date") and not g["releaseDate"]:
            # Format release date YYYY-MM-DD if possible
            m = re.match(r"(\d{2})/(\d{2})/(\d{4})", c["release_date"])
            if m:
                g["releaseDate"] = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"

    # 2. Ingest Co-Optimus 3DS
    for c in coop_3ds:
        plat = c.get("platform", "3ds")
        if plat not in ("3ds", "ds"):
            plat = "3ds"
        g = get_or_create_game(c["title"], plat)
        g["sources"].append(f"cooptimus:{plat}")
        if c.get("url"):
            g["ids"]["cooptimusUrl"] = c["url"]

        if c.get("local_max"):
            cur = g["coop"]["localWireless"]["max"] or 0
            g["coop"]["localWireless"]["max"] = max(cur, c["local_max"])

        if c.get("online_max"):
            cur = g["coop"]["online"]["max"] or 0
            g["coop"]["online"]["max"] = max(cur, c["online_max"])

        if c.get("campaign"):
            g["coop"]["campaign"] = True
        if c.get("drop_in_out") is not None:
            g["coop"]["dropInOut"] = c["drop_in_out"]

    # 3. Ingest Curated Download Play (highest precedence for 3DS/DS Download Play)
    for dp in dl_play_yaml:
        title = dp["title"]
        plat = dp.get("platform", "3ds")
        g = get_or_create_game(title, plat)
        g["sources"].append("curated:download_play")
        g["coop"]["downloadPlay"] = True

        if dp.get("mode") in ("versus", "both"):
            g["versus"] = True

        p_max = dp.get("maxPlayers")
        if p_max:
            cur = g["coop"]["localWireless"]["max"] or 0
            g["coop"]["localWireless"]["max"] = max(cur, p_max)

        if dp.get("notes"):
            g["editorial"]["setupGuide"] = (
                f"Supports Nintendo {plat.upper()} single-cartridge Download Play: {dp['notes']}"
            )

    # 4. Attach Switch TitleDB metadata & art
    for title, meta in switch_meta.items():
        norm = normalize_title(title)
        if norm in games_by_norm:
            g = games_by_norm[norm]
            g["sources"].append("titledb:switch")
            tid = meta.get("switchTitleId")
            if tid and re.match(r"^[0-9A-Fa-f]{16}$", tid):
                g["ids"]["switchTitleId"] = tid.upper()
            if meta.get("nsuId"):
                g["ids"]["nsuId"] = meta["nsuId"]
            if meta.get("publisher") and not g["publisher"]:
                g["publisher"] = meta["publisher"]
            if meta.get("releaseDate") and not g["releaseDate"]:
                g["releaseDate"] = meta["releaseDate"]
            if meta.get("genres"):
                for genre in meta["genres"]:
                    if genre and genre not in g["genres"]:
                        g["genres"].append(genre)
            if meta.get("iconUrl") and not g["cover"]:
                g["cover"] = {"url": meta["iconUrl"], "source": "titledb"}
            if meta.get("description") and "engaging cooperative" in g["editorial"]["summary"]:
                desc = meta["description"].replace("\r\n", " ").strip()
                sentences = re.split(r"(?<=[.!?]) +", desc)
                if sentences and len(sentences[0]) > 10:
                    g["editorial"]["summary"] = " ".join(sentences[:2])[:350]

    # 5. Attach 3DS TitleDB metadata & box art
    for title, meta in ctr_meta.items():
        norm = normalize_title(title)
        if norm in games_by_norm:
            g = games_by_norm[norm]
            g["sources"].append("titledb:3ds")
            if meta.get("ctrProductCode"):
                g["ids"]["ctrProductCode"] = meta["ctrProductCode"]
            if meta.get("coverUrl") and not g["cover"]:
                g["cover"] = {"url": meta["coverUrl"], "source": "gametdb"}

    # 6. Apply Legacy Curated (human-verified setup guides & picks)
    for norm, leg in legacy_map.items():
        if norm in games_by_norm:
            g = games_by_norm[norm]
            g["sources"].append("seed:legacy")
            g["curatorPick"] = True
            if leg.get("setupGuide"):
                g["editorial"]["setupGuide"] = leg["setupGuide"]
            if leg.get("multiplayerFeatures"):
                g["editorial"]["coopSummary"] = leg["multiplayerFeatures"]
            if leg.get("vibe") in ["Cozy", "Story", "Chaos", "Puzzle", "Action", "Competitive"]:
                g["editorial"]["vibe"] = leg["vibe"]
            if leg.get("difficulty") in ["Very Chill", "Low", "Medium", "Hard"]:
                g["editorial"]["difficulty"] = leg["difficulty"]
            if leg.get("isCouplePick"):
                g["editorial"]["audiences"] = ["couples", "friends"]

    # 7. Apply Backloggd list as curator pick signal
    for norm in backloggd_picks:
        if norm in games_by_norm:
            games_by_norm[norm]["curatorPick"] = True

    # 8. Post-processing: Compute maxPlayers, deduplicate IDs, filter valid multiplayer titles
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    compiled_games = []
    used_ids: Set[str] = set()

    # Load JSON schema validator
    schema = load_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)

    schema_errors = 0
    discarded_no_mp = 0

    for norm, g in games_by_norm.items():
        loc_max = g["coop"]["local"]["max"] or 0
        wir_max = g["coop"]["localWireless"]["max"] or 0
        onl_max = g["coop"]["online"]["max"] or 0
        dl_play = g["coop"]["downloadPlay"]

        # Drop games with no multiplayer evidence (all players <= 1 and no Download Play)
        total_p_max = max(loc_max, wir_max, onl_max)
        if total_p_max <= 1 and not dl_play:
            discarded_no_mp += 1
            continue

        g["maxPlayers"] = total_p_max if total_p_max > 1 else (2 if dl_play else None)
        g["platforms"] = sorted(list(g["platforms"]))

        # Build stable ID
        base_slug = slugify(g["title"])
        game_id = base_slug
        if game_id in used_ids:
            game_id = f"{base_slug}-{g['platforms'][0]}"
            counter = 2
            while game_id in used_ids:
                game_id = f"{base_slug}-{counter}"
                counter += 1
        used_ids.add(game_id)
        g["id"] = game_id

        # Defaults for empty genres
        if not g["genres"]:
            g["genres"] = ["Action-Adventure"]

        # Validate releaseDate format (YYYY-MM-DD or YYYY)
        rd = g.get("releaseDate")
        if rd and not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", rd):
            m = re.match(r"\b(\d{4})\b", rd)
            g["releaseDate"] = m.group(1) if m else None

        g["updatedAt"] = now_iso

        # Apply human overrides if configured
        if game_id in overrides:
            ov = overrides[game_id]
            if ov.get("_exclude"):
                continue

            def deep_merge(target: dict, source: dict):
                for k, v in source.items():
                    if k == "_exclude":
                        continue
                    if isinstance(v, dict) and isinstance(target.get(k), dict):
                        deep_merge(target[k], v)
                    else:
                        target[k] = v

            deep_merge(g, ov)

        # Remove internal fields not in schema
        g.pop("norm", None)

        # Validate against schema
        errors = list(validator.iter_errors(g))
        if errors:
            schema_errors += 1
            print(f"[!] Schema error in {g['id']}: {errors[0].message}")
            continue

        compiled_games.append(g)

    # Sort compiled database by title
    compiled_games.sort(key=lambda x: x["title"].lower())

    # Save to data/build/games.base.json
    out_path = BUILD / "games.base.json"
    save_json(out_path, compiled_games)

    # Generate Markdown Report
    switch_count = sum(1 for x in compiled_games if "switch" in x["platforms"])
    s2_count = sum(1 for x in compiled_games if "switch2" in x["platforms"])
    p3ds_count = sum(1 for x in compiled_games if "3ds" in x["platforms"])
    pds_count = sum(1 for x in compiled_games if "ds" in x["platforms"])
    dl_count = sum(1 for x in compiled_games if x["coop"]["downloadPlay"])
    curator_count = sum(1 for x in compiled_games if x["curatorPick"])
    covers_count = sum(1 for x in compiled_games if x.get("cover"))

    report_lines = [
        "# DuoPlay Database Compilation Report",
        "",
        f"**Generated at:** {now_iso}",
        "",
        "## Summary Metrics",
        f"- **Total Games Compiled:** {len(compiled_games)}",
        f"- **Nintendo Switch Titles:** {switch_count}",
        f"- **Nintendo Switch 2 Titles:** {s2_count}",
        f"- **Nintendo 3DS Titles:** {p3ds_count}",
        f"- **Nintendo DS Titles:** {pds_count}",
        f"- **Download Play (Single-Cart) Titles:** {dl_count}",
        f"- **Curator's Picks:** {curator_count}",
        f"- **Games with Artwork/Cover:** {covers_count} ({covers_count/len(compiled_games)*100:.1f}%)",
        f"- **Discarded (Single-player only):** {discarded_no_mp}",
        f"- **Schema Validation Errors:** {schema_errors}",
        "",
        "## Data Sources Used",
        "- Co-Optimus Switch (`cooptimus_switch.norm.json`)",
        "- Co-Optimus 3DS (`cooptimus_3ds.norm.json`)",
        "- Switch TitleDB community database (`switch_titledb.json`)",
        "- GhostLand / GameTDB 3DS database (`3ds_titledb.json`)",
        "- Curated 3DS/DS Download Play catalog (`download_play_3ds.yaml`)",
        "- Hand-verified seed catalog (`legacy_curated.json`)",
        "- Backloggd Co-Op list (`backloggd_titles.txt`)",
        "",
        "## Status",
        "✓ All compiled records successfully validated against `pipeline/schema/game.schema.json`.",
    ]

    report_path = BUILD / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\n[✓] Successfully compiled {len(compiled_games)} games to {out_path}!")
    print(f"[✓] Written build report to {report_path}")
    return {
        "total": len(compiled_games),
        "switch": switch_count,
        "3ds": p3ds_count,
        "downloadPlay": dl_count,
        "covers": covers_count,
    }


if __name__ == "__main__":
    build_unified_database()
