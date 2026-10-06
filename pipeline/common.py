"""Shared helpers for the DuoPlay data pipeline: title normalization, slugs, and I/O."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
CURATED = DATA / "curated"
SEED = DATA / "seed"
BUILD = DATA / "build"
CACHE = DATA / "cache"
SCHEMA_PATH = ROOT / "pipeline" / "schema" / "game.schema.json"

# Suffixes that denote a re-release / storefront label rather than a different game.
_EDITION_SUFFIXES = [
    r"nintendo switch 2 edition",
    r"nintendo switch edition",
    r"switch edition",
    r"for nintendo switch",
    r"for nintendo 3ds",
    r"complete edition",
    r"definitive edition",
    r"deluxe edition",
    r"game of the year edition",
    r"goty edition",
    r"anniversary edition",
    r"remastered",
    r"hd",
]

# Titles where a word that looks like an edition marker is part of the canonical name.
_CANONICAL_ALLOWLIST = {
    "mario kart 8 deluxe",
    "new super mario bros u deluxe",
    "kirbys return to dream land deluxe",
    "pikmin 3 deluxe",
    "captain toad treasure tracker",
    "castle crashers remastered",
    "the legend of zelda links awakening",
}

_PUNCT_MAP = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u00b7": " ", "&": " and ",
})


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _basic(title: str) -> str:
    t = title.translate(_PUNCT_MAP)
    t = re.sub(r"[\u2122\u00ae\u00a9]", "", t)  # ™ ® ©
    t = _strip_accents(t).lower()
    t = t.replace("'", "")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_title(title: str) -> str:
    """Normalize a game title for matching across sources.

    Lowercases, strips trademark symbols/accents/punctuation, and removes edition or
    storefront suffixes unless the full title is on the canonical allowlist.
    """
    t = _basic(title)
    if t in _CANONICAL_ALLOWLIST:
        return t
    changed = True
    while changed:
        changed = False
        for suf in _EDITION_SUFFIXES:
            new = re.sub(rf"(?:\s|^){suf}$", "", t).strip()
            if new != t and new:
                if t in _CANONICAL_ALLOWLIST:
                    break
                t, changed = new, True
    return t


def slugify(title: str) -> str:
    s = _basic(title)
    return re.sub(r"\s+", "-", s) or "game"


def load_json(path: Path | str) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path | str, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_yaml(path: Path | str) -> Any:
    import yaml

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
