from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from keezboard.engine import GameState, from_dict, to_dict


class StateStore:
    def __init__(self, path: str | Path | None = None) -> None:
        configured_path = path or os.environ.get("KEEZBOARD_DB", "keezboard.sqlite3")
        self.path = Path(configured_path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS active_game (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        payload TEXT NOT NULL
                    )
                    """
                )

    def load(self) -> GameState | None:
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute(
                "SELECT payload FROM active_game WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        return from_dict(json.loads(row[0]))

    def save(self, state: GameState) -> None:
        payload = json.dumps(to_dict(state), separators=(",", ":"))
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute(
                    """
                    INSERT INTO active_game (id, payload) VALUES (1, ?)
                    ON CONFLICT(id) DO UPDATE SET payload = excluded.payload
                    """,
                    (payload,),
                )
