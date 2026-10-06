from pipeline.common import BUILD, load_json


def test_compiled_database_schema():
    base_json = BUILD / "games.base.json"
    assert base_json.exists(), "games.base.json was not built"
    games = load_json(base_json)

    assert len(games) > 2000
    mario_kart_7 = next((g for g in games if g["id"] == "mario-kart-7"), None)
    assert mario_kart_7 is not None
    assert "3ds" in mario_kart_7["platforms"]
    assert mario_kart_7["coop"]["downloadPlay"] is True

    it_takes_two = next((g for g in games if g["id"] == "it-takes-two"), None)
    assert it_takes_two is not None
    assert "switch" in it_takes_two["platforms"]
    assert it_takes_two["coop"]["campaign"] is True
    assert it_takes_two["coop"]["local"]["splitScreen"] is True

    # Check for duplicate IDs
    ids = [g["id"] for g in games]
    assert len(ids) == len(set(ids)), "Duplicate game IDs found in database"
