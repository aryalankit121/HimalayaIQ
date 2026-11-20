"""Load reviewed JSON into SQLite; seed edits refresh the cache transactionally."""

from dataclasses import asdict
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from .models import Trek
from .validation import validate_trek

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "treks.json"
DB_PATH = ROOT / "data" / "himalayaiq.sqlite3"


def read_seed(path: Path = SEED_PATH) -> list[Trek]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("Trek dataset must contain a nonempty list.")
    treks = [Trek(**record) for record in records]
    for trek in treks:
        validate_trek(trek)
    if len({trek.id for trek in treks}) != len(treks):
        raise ValueError("Trek IDs must be unique.")
    return treks


def load_treks(db_path: Path = DB_PATH, seed_path: Path = SEED_PATH) -> list[Trek]:
    treks = read_seed(seed_path)
    digest = hashlib.sha256(seed_path.read_bytes()).hexdigest()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
        connection.execute("CREATE TABLE IF NOT EXISTS treks (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        stored = connection.execute("SELECT value FROM metadata WHERE key = 'seed_hash'").fetchone()
        count = connection.execute("SELECT COUNT(*) FROM treks").fetchone()[0]
        if stored != (digest,) or count != len(treks):
            connection.execute("DELETE FROM treks")
            connection.executemany("INSERT INTO treks VALUES (?, ?)", [
                (trek.id, json.dumps(asdict(trek))) for trek in treks
            ])
            connection.execute("INSERT OR REPLACE INTO metadata VALUES ('seed_hash', ?)", (digest,))
        rows = connection.execute("SELECT data FROM treks ORDER BY id").fetchall()
    result = [Trek(**json.loads(row[0])) for row in rows]
    for trek in result:
        validate_trek(trek)
    return result
