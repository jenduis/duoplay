import json
from pathlib import Path

from scrapers.cooptimus import normalize_record


def test_normalize_record_fixtures():
    fixture_path = Path(__file__).parent / "fixtures" / "cooptimus_sample.json"
    with open(fixture_path, encoding="utf-8") as f:
        samples = json.load(f)

    # It Takes Two
    itt = normalize_record(samples[0])
    assert itt["title"] == "It Takes Two"
    assert itt["platform"] == "switch"
    assert itt["local_max"] == 2
    assert itt["online_max"] == 2
    assert itt["split_screen"] is True
    assert itt["campaign"] is True
    assert itt["drop_in_out"] is True

    # Mario Kart 8 Deluxe
    mk8 = normalize_record(samples[1])
    assert mk8["title"] == "Mario Kart 8 Deluxe"
    assert mk8["local_max"] == 4
    assert mk8["online_max"] == 12
    assert mk8["split_screen"] is True

    # Luigi's Mansion 3DS
    lm = normalize_record(samples[2])
    assert lm["platform"] == "3ds"
    assert lm["local_max"] == 4
    assert lm["campaign"] is True

    # Unknown
    unk = normalize_record(samples[4])
    assert unk["local_max"] is None
    assert unk["online_max"] is None
    assert unk["campaign"] is False
