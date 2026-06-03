# -*- coding: utf-8 -*-
"""SQLite persistence for FullPet state and achievements."""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from utils.paths import data_dir

_log = logging.getLogger(__name__)

_CREATE_PET_STATE = """
    CREATE TABLE IF NOT EXISTS pet_state (
        id          INTEGER PRIMARY KEY,
        name        TEXT,
        pet_type    TEXT,
        hunger      REAL,
        happiness   REAL,
        energy      REAL,
        health      REAL,
        level       INTEGER,
        exp         INTEGER,
        position_x  INTEGER,
        position_y  INTEGER,
        last_save   TEXT
    )
"""

_CREATE_ACHIEVEMENTS = """
    CREATE TABLE IF NOT EXISTS achievements (
        id               INTEGER PRIMARY KEY,
        achievement_id   TEXT UNIQUE,
        unlocked_date    TEXT,
        description      TEXT
    )
"""


class PetDatabase:
    """SQLite-backed store for a single FullPet's state and achievements."""

    def __init__(self) -> None:
        self.db_path: Path = data_dir() / "pet_data.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(_CREATE_PET_STATE)
            conn.execute(_CREATE_ACHIEVEMENTS)

    # ------------------------------------------------------------------
    # Pet state
    # ------------------------------------------------------------------

    def save_pet(self, data: dict) -> None:
        """Atomically replace the single pet-state record."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM pet_state")
                conn.execute(
                    """INSERT INTO pet_state
                       (name, pet_type, hunger, happiness, energy, health,
                        level, exp, position_x, position_y, last_save)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        data["name"],       data["pet_type"],
                        data["hunger"],     data["happiness"],
                        data["energy"],     data["health"],
                        data["level"],      data["exp"],
                        data["position_x"], data["position_y"],
                        data["last_save"],
                    ),
                )
        except sqlite3.Error as exc:
            _log.error("Failed to save pet state: %s", exc)

    def load_pet(self) -> dict | None:
        """Return the stored pet-state dict, or None if the table is empty."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT * FROM pet_state LIMIT 1"
                ).fetchone()
        except sqlite3.Error as exc:
            _log.error("Failed to load pet state: %s", exc)
            return None

        if row is None:
            return None

        return {
            "name":       row[1],
            "pet_type":   row[2],
            "hunger":     row[3],
            "happiness":  row[4],
            "energy":     row[5],
            "health":     row[6],
            "level":      row[7],
            "exp":        row[8],
            "position_x": row[9],
            "position_y": row[10],
            "last_save":  row[11],
        }

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    def save_achievement(self, achievement_id: str, description: str) -> bool:
        """Insert a new achievement. Returns False if it already exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO achievements
                       (achievement_id, unlocked_date, description)
                       VALUES (?,?,?)""",
                    (achievement_id, datetime.now().isoformat(), description),
                )
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as exc:
            _log.error("Failed to save achievement %r: %s", achievement_id, exc)
            return False

    def get_achievements(self) -> list[dict]:
        """Return all unlocked achievements ordered by date."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    "SELECT * FROM achievements ORDER BY unlocked_date"
                ).fetchall()
        except sqlite3.Error as exc:
            _log.error("Failed to load achievements: %s", exc)
            return []

        return [
            {"id": row[1], "date": row[2], "description": row[3]}
            for row in rows
        ]

    def clear_data(self) -> None:
        """Delete all pet state and achievement records."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM pet_state")
                conn.execute("DELETE FROM achievements")
        except sqlite3.Error as exc:
            _log.error("Failed to clear data: %s", exc)
