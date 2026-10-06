import json

import jsonschema
import pytest

from common import SCHEMA_PATH, normalize_title, slugify


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Pokémon\u2122 Scarlet", "pokemon scarlet"),
        ("Overcooked! 2", "overcooked 2"),
        ("Overcooked 2", "overcooked 2"),
        ("Luigi\u2019s Mansion 3", "luigis mansion 3"),
        ("Luigi's Mansion 3", "luigis mansion 3"),
        ("Mario Kart 8 Deluxe", "mario kart 8 deluxe"),
        ("Pikmin 3 Deluxe", "pikmin 3 deluxe"),
        ("Bread & Fred", "bread and fred"),
        ("Stardew Valley \u2014 Nintendo Switch Edition", "stardew valley"),
        ("Hades for Nintendo Switch", "hades"),
        ("Cuphead Deluxe Edition", "cuphead"),
        ("Castle Crashers Remastered", "castle crashers remastered"),
        ("  Super   Mario Party  ", "super mario party"),
    ],
)
def test_normalize_title(raw, expected):
    assert normalize_title(raw) == expected


def test_slugify():
    assert slugify("Mario Kart 7") == "mario-kart-7"
    assert slugify("Kirby\u2122: Planet Robobot") == "kirby-planet-robobot"
    assert slugify("!!!") == "game"


def test_schema_is_valid():
    schema = json.loads(SCHEMA_PATH.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
