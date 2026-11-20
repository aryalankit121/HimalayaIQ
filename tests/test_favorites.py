import json
import sqlite3

import pytest

from himalayaiq.database import SEED_PATH, load_treks
from himalayaiq.favorites import favorite_ids, remove_favorite, save_favorite


def test_persistence_idempotence_and_removal(tmp_path):
    db = tmp_path / "test.sqlite3"
    load_treks(db)
    save_favorite("langtang-valley", db)
    save_favorite("langtang-valley", db)
    assert favorite_ids(db) == ["langtang-valley"]
    # Separate connection proves persistence beyond a UI session.
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM favorites").fetchone()[0] == 1
    remove_favorite("langtang-valley", db)
    remove_favorite("langtang-valley", db)
    assert favorite_ids(db) == []


def test_catalog_refresh_does_not_erase_favorites(tmp_path):
    db, seed = tmp_path / "test.sqlite3", tmp_path / "seed.json"
    records = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    seed.write_text(json.dumps(records))
    load_treks(db, seed)
    save_favorite("langtang-valley", db)
    records[0]["summary"] += " Updated."
    seed.write_text(json.dumps(records))
    load_treks(db, seed)
    assert favorite_ids(db) == ["langtang-valley"]


@pytest.mark.parametrize("trek_id", ["", "unknown", "' OR 1=1 --"])
def test_invalid_ids(tmp_path, trek_id):
    db = tmp_path / "test.sqlite3"
    load_treks(db)
    with pytest.raises(ValueError):
        save_favorite(trek_id, db)
    assert favorite_ids(db) == []
