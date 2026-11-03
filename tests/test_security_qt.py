"""User text stays text; recovery and core Qt6 interaction stay compatible."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from pet.full_pet import FullPet
from ui.stats_widget import StatsWindow

NAME = '<b>literal</b><img src="file:///never-load">'


def test_names_remain_plain_in_settings_and_interaction_menu(window, qt_app):
    window.pet.name = NAME
    window._add_satellite('panda')
    window._satellites[0].pet.name = NAME
    window._show_settings()
    labels = [label for label in window.settings_window.findChildren(QLabel) if NAME in label.text()]
    assert labels and all(label.textFormat() == Qt.TextFormat.PlainText for label in labels)
    for style in ('panel', 'ring'):
        window.settings_store.menu_style = style
        window._show_context_menu(window.pos())
        heading = next(label for label in window.interaction_panel.findChildren(QLabel) if label.text() == NAME)
        assert heading.textFormat() == Qt.TextFormat.PlainText
        window._close_interaction_panel()


def test_stats_user_name_is_plain_text(qt_app, db):
    pet = FullPet('fox', NAME, db)
    stats = StatsWindow(pet)
    try:
        label = next(label for label in stats.findChildren(QLabel) if NAME in label.text())
        assert label.textFormat() == Qt.TextFormat.PlainText
    finally:
        stats.close()
        stats.deleteLater()
        pet.cleanup()


def test_startup_preserves_corrupt_roster_until_settings_apply(qt_app):
    from tests.conftest import MemoryBackend
    from ui.pet_window import PetWindow
    from utils.settings_store import SettingsStore
    backend = MemoryBackend({'pet': 'panda', 'pets': '[' * 4000 + '0' + ']' * 4000})
    store = SettingsStore(backend)
    store.load()
    window = PetWindow(settings_store=store, restore=True)
    try:
        original = backend.values['pets']
        window.persist_state()
        window.hide()
        window.show()
        assert backend.values['pets'] == original
        window._show_settings()
        window.settings_window._apply()
        assert backend.values['pets'] != original
    finally:
        window._shutdown()
        window.deleteLater()
