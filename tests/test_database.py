"""Unit tests for PetDatabase."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Provide a PetDatabase backed by a temporary file."""
    from utils import paths as _paths

    monkeypatch.setattr(_paths, "data_dir", lambda: tmp_path)
    from utils.database import PetDatabase
    return PetDatabase()


class TestPetDatabase:
    def test_save_and_load(self, db):
        data = {
            "name": "Rex",
            "pet_type": "fox",
            "hunger": 75.0,
            "happiness": 60.0,
            "energy": 90.0,
            "health": 100.0,
            "level": 3,
            "exp": 42,
            "position_x": 200,
            "position_y": 150,
            "last_save": "2026-01-01T00:00:00",
        }
        db.save_pet(data)
        loaded = db.load_pet()
        assert loaded is not None
        assert loaded["name"] == "Rex"
        assert loaded["level"] == 3
        assert abs(loaded["hunger"] - 75.0) < 1e-6

    def test_load_empty_returns_none(self, db):
        assert db.load_pet() is None

    def test_clear_data(self, db):
        db.save_pet({
            "name": "Rex", "pet_type": "fox",
            "hunger": 100.0, "happiness": 100.0,
            "energy": 100.0, "health": 100.0,
            "level": 1, "exp": 0,
            "position_x": 0, "position_y": 0,
            "last_save": "2026-01-01T00:00:00",
        })
        db.clear_data()
        assert db.load_pet() is None

    def test_no_cat_in_type(self, db):
        data = {
            "name": "Test", "pet_type": "fox",
            "hunger": 100.0, "happiness": 100.0,
            "energy": 100.0, "health": 100.0,
            "level": 1, "exp": 0,
            "position_x": 0, "position_y": 0,
            "last_save": "2026-01-01T00:00:00",
        }
        db.save_pet(data)
        loaded = db.load_pet()
        assert loaded["pet_type"] != "cat"
