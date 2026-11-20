"""Device-local favorites. Additive schema; no changes to existing trek tables."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

from .database import DB_PATH


@contextmanager
def favorites_connection(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path, timeout=10) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS favorites (
            trek_id TEXT PRIMARY KEY, saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        yield connection


def favorite_ids(db_path: Path = DB_PATH) -> list[str]:
    with favorites_connection(db_path) as connection:
        return [row[0] for row in connection.execute(
            "SELECT trek_id FROM favorites ORDER BY saved_at, trek_id")]


def save_favorite(trek_id: str, db_path: Path = DB_PATH) -> None:
    if not isinstance(trek_id, str) or not trek_id.strip():
        raise ValueError("Choose a valid trek to save.")
    with favorites_connection(db_path) as connection:
        if not connection.execute("SELECT 1 FROM treks WHERE id = ?", (trek_id,)).fetchone():
            raise ValueError("This trek is no longer in the catalog. Refresh and choose another.")
        connection.execute("INSERT OR IGNORE INTO favorites (trek_id) VALUES (?)", (trek_id,))


def remove_favorite(trek_id: str, db_path: Path = DB_PATH) -> None:
    with favorites_connection(db_path) as connection:
        connection.execute("DELETE FROM favorites WHERE trek_id = ?", (trek_id,))
