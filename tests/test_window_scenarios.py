"""User workflows using only the fixture's memory settings and temporary DB."""
from PyQt6.QtCore import QPoint, QCoreApplication, QEvent
from PyQt6 import sip

from ui.pet_window import PetWindow
from utils.geometry import available_rect
from utils.settings_store import SettingsStore, store


def test_language_change_rebuilds_tray(window, isolated_persistence, qt_app):
    window._show_settings()
    settings = window.settings_window
    previous = window.tray_manager.tray.contextMenu()
    settings._set_language("en")
    assert store.lang == "en"
    assert window.tray_manager.tray.contextMenu() is not previous
    assert "Hide" in window.tray_manager._tray_toggle_action.text()
    settings.close()
    assert not settings._anim_timer.isActive()
    settings.show()
    assert settings._anim_timer.isActive()


def test_satellite_apply_preserves_primary_and_restores_roster(window, qt_app):
    window.pet.name = "Main"
    window._add_satellite("panda")
    satellite = window._satellites[0]
    satellite._show_settings()
    settings = satellite.settings_window
    settings.name_input.setText("Extra")
    settings._select_card("dog")
    settings._apply()
    assert not settings._anim_timer.isActive()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    assert sip.isdeleted(settings)
    assert window.pet.pet_type == "fox"
    assert satellite.pet.pet_type == "dog"
    assert satellite.pet.name == "Extra"
    assert satellite.settings_window is None
    assert store.roster()[0]["type"] == "fox"
    assert store.roster()[1]["type"] == "dog"


def test_shutdown_roundtrip_and_removed_satellite(window, qt_app, isolated_persistence):
    window.pet.name = "Main"
    window._add_satellite("panda")
    window._add_satellite("dog")
    window._satellites[0].pet.name = "First"
    window._satellites[1].pet.name = "Second"
    window._satellites[0].hide()
    window.persist_state()
    expected = store.roster()
    old_satellites = list(window._satellites)
    window._shutdown()
    assert all(not sat.isVisible() for sat in old_satellites)
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert all(sip.isdeleted(sat) for sat in old_satellites)
    assert store.roster() == expected
    loaded = SettingsStore(isolated_persistence)
    loaded.load()
    restored = PetWindow(settings_store=loaded, restore=True)
    try:
        assert [w.pet.name for w in [restored] + restored._satellites] == ["Main", "First", "Second"]
        restored._satellites[0]._remove_self()
        restored._shutdown()
        loaded.load()
        assert [p["name"] for p in loaded.roster()] == ["Main", "Second"]
    finally:
        restored._shutdown()
        restored.hide()
        restored.deleteLater()
        qt_app.processEvents()


def test_edge_position_roundtrips_exactly(window, qt_app, isolated_persistence):
    rect = available_rect(window.pos())
    edge = QPoint(rect.right() - window.width() + 1, rect.bottom() - window.height() + 1)
    window.move(edge)
    window._shutdown()
    loaded = SettingsStore(isolated_persistence)
    loaded.load()
    restored = PetWindow(settings_store=loaded, restore=True)
    try:
        assert restored.pos() == edge
    finally:
        restored._shutdown()
        restored.hide()
        restored.deleteLater()


def test_hide_resume_switch_remove_cleanup(window, qt_app, monkeypatch):
    window._throw_ball(window.x(), window.y(), window.x() + 100, window.y() - 50)
    old_ball = window.ball_widget
    window.hide()
    assert not old_ball.timer.isActive()
    assert not old_ball.isVisible()
    assert not window.ball.active
    assert not window.pet.is_chasing
    assert all(not timer.isActive() for timer in
               (window._animation_timer, window._state_timer, window._behavior_timer, window._mouse_timer))
    window.show()
    assert window._animation_timer.isActive()
    assert not window._state_timer.isActive()  # SimplePet has no stats work.
    import ui.pet_window as module
    window._last_tick = -1000000
    monkeypatch.setattr(module, "monotonic", lambda: 1000.0)
    window.hide()
    window.show()
    window.pet.chase(window.x() + 200, window.y())
    before = window.pos()
    window._update_animation()
    assert window.pos() == before  # Resume reset elapsed time.
    window._throw_ball(window.x(), window.y(), window.x() + 100, window.y() - 50)
    old_ball = window.ball_widget
    window.set_pet_type("panda")
    assert not old_ball.timer.isActive()
    assert window.ball_widget is None
    window._add_satellite("dog")
    sat = window._satellites[0]
    sat._throw_ball(sat.x(), sat.y(), sat.x() + 100, sat.y() - 50)
    widget = sat.ball_widget
    sat.close()
    assert sat not in window._satellites
    assert not widget.timer.isActive()
    assert not sat._animation_timer.isActive()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert sip.isdeleted(widget)
    assert sip.isdeleted(sat)


def test_sleep_ends_throw_and_chase(window):
    window._throw_ball(window.x(), window.y(), window.x() + 100, window.y() - 50)
    widget = window.ball_widget
    window._sleep()
    assert not widget.timer.isActive()
    assert not widget.isVisible()
    assert not window.pet.is_chasing
    assert window.pet.state == "lie"


def test_unchanged_frame_does_not_repaint_pixmap(window, monkeypatch):
    import ui.pet_window as module
    calls = []
    original = window.sprite_label.setPixmap
    monkeypatch.setattr(window.sprite_label, "setPixmap", lambda px: (calls.append(px.cacheKey()), original(px)))
    now = window._last_tick
    monkeypatch.setattr(module, "monotonic", lambda: now)
    window._update_animation()
    window._update_animation()
    assert not calls
    window.pet.facing_right = not window.pet.facing_right
    window._update_animation()
    assert len(calls) == 1
    window._update_animation()
    assert len(calls) == 1
