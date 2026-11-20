import json
import sqlite3

import pytest

from himalayaiq.database import SEED_PATH, load_treks


def test_seed_idempotence_and_refresh(tmp_path):
    seed = tmp_path / "treks.json"
    seed.write_bytes(SEED_PATH.read_bytes())
    db = tmp_path / "treks.sqlite3"
    assert len(load_treks(db, seed)) == 6
    assert len(load_treks(db, seed)) == 6
    records = json.loads(seed.read_text())
    records[0]["cost_max"] = 1100
    seed.write_text(json.dumps(records))
    assert next(t for t in load_treks(db, seed) if t.id == "langtang-valley").cost_max == 1100
    records[0]["cost_min"] = -1
    seed.write_text(json.dumps(records))
    with pytest.raises(ValueError):
        load_treks(db, seed)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM treks").fetchone()[0] == 6


def test_duplicate_id_rejected(tmp_path):
    records = json.loads(SEED_PATH.read_text())
    records[1]["id"] = records[0]["id"]
    seed = tmp_path / "bad.json"
    seed.write_text(json.dumps(records))
    with pytest.raises(ValueError, match="unique"):
        load_treks(tmp_path / "treks.sqlite3", seed)
