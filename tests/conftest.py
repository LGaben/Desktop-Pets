"""All tests use temporary persistence; no user registry or database access."""
import os
from copy import deepcopy

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


class MemoryBackend:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.writes = 0

    def read(self):
        return deepcopy(self.values)

    def write(self, values):
        self.values.update(deepcopy(values))
        self.writes += 1


@pytest.fixture(autouse=True)
def isolated_persistence(tmp_path, monkeypatch):
    from utils import paths
    from utils.settings_store import store
    backend = MemoryBackend()
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(store, "backend", backend)
    monkeypatch.setattr(store, "lang", "ru")
    monkeypatch.setattr(store, 'menu_style', 'panel')
    monkeypatch.setattr(store, "pets", [{"type": "fox"}])
    return backend


@pytest.fixture
def db(tmp_path):
    from utils.database import PetDatabase
    return PetDatabase(tmp_path / "test-pet.db")


@pytest.fixture(scope="session")
def qt_app():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def window(qt_app):
    from ui.pet_window import PetWindow
    window = PetWindow()
    yield window
    window._shutdown()
    window.hide()
    window.deleteLater()
    from PyQt6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
