"""Native menu and movement integration; requires a compatible Qt runtime."""
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMenu, QPushButton, QScrollArea

from pet.simple_pet import SimplePet
from ui.interaction_panel import InteractionPanel
from ui.menu_style import add_menu_style
from utils.i18n import t
from utils.settings_store import store


@pytest.mark.parametrize('style', ['panel', 'ring'])
@pytest.mark.parametrize('lang', ['ru', 'en'])
def test_menu_styles_keep_all_actions_and_keyboard_access(window, monkeypatch, style, lang):
    import ui.interaction_panel as module
    monkeypatch.setattr(module, 'available_rect', lambda _: QRect(-1200, -700, 1000, 700))
    store.lang, store.menu_style = lang, style
    window._show_context_menu(QPoint(-210, -20))
    panel = window.interaction_panel
    QApplication.processEvents()
    assert panel.menu_style == style
    assert panel._radial == (style == 'ring')
    assert QRect(-1200, -700, 1000, 700).contains(panel.geometry())
    buttons = panel.findChildren(QPushButton)
    assert {button.accessibleName() for button in buttons} >= {
        t('pet_action'), t('ball_action'), t('sleep'), t('settings'), t('start_follow'),
        t('hide_to_tray'), t('quit')}
    assert not panel.findChildren(QMenu)
    assert all(button.height() >= 44 for button in buttons)
    first = panel.findChild(QPushButton)
    QTest.keyClick(first, Qt.Key.Key_Tab)
    assert QApplication.focusWidget() in buttons
    assert QApplication.focusWidget() is not first
    QTest.keyClick(panel, Qt.Key.Key_Escape)
    assert not panel.isVisible()


@pytest.mark.parametrize('height', [120, 180])
@pytest.mark.parametrize('labels', ['short', 'ru', 'en'])
def test_tiny_work_area_uses_scrollable_actions_without_clipping(qt_app, monkeypatch, height, labels):
    import ui.interaction_panel as module
    bounds = QRect(-250, -200, 200, height)
    monkeypatch.setattr(module, 'available_rect', lambda _: bounds)
    calls = []
    if labels == 'short':
        names = [str(n) for n in range(6)]
    else:
        store.lang = labels
        names = [t(key) for key in ('pet_action', 'ball_action', 'sleep', 'settings', 'start_follow', 'hide_to_tray')]
    panel = InteractionPanel(None, 'Pet', '', [(name, lambda: calls.append(1)) for name in names], 'ring')
    try:
        panel.ensurePolished()
        body = panel._scroll.widget()
        body.ensurePolished()
        body.layout().activate()
        required = body.sizeHint().expandedTo(body.minimumSizeHint()) + QSize(16, 16)
        fits_ring = required.width() <= bounds.width() and required.height() <= bounds.height()
        panel.open_at(QPoint(-51, -21))
        qt_app.processEvents()
        assert panel._radial and panel.menu_style == 'ring'
        assert panel._compact == (not fits_ring)
        if height == 120:
            assert panel._compact
        assert bounds.contains(panel.geometry())
        if not fits_ring:
            assert panel.findChild(QScrollArea).verticalScrollBar().maximum() > 0
        first_action = next(button for button in panel.findChildren(QPushButton)
                            if button.accessibleName() == names[0])
        panel._scroll.ensureWidgetVisible(first_action)
        qt_app.processEvents()
        QTest.mouseClick(first_action, Qt.MouseButton.LeftButton)
        assert calls == [1] and not panel.isVisible()
    finally:
        panel.close()
        panel.deleteLater()


def test_style_selector_is_global_in_tray_and_popup_and_closes_popups(window, isolated_persistence, monkeypatch):
    from PyQt6.QtWidgets import QMenu
    window._add_satellite('panda')
    satellite = window._satellites[0]
    window._show_context_menu(window.pos())
    satellite._show_context_menu(satellite.pos())
    menu = window.tray_manager.tray.contextMenu()
    selector = next(action.menu() for action in menu.actions() if action.text() == t('menu_style'))
    ring = next(action for action in selector.actions() if action.data() == 'ring')
    ring.trigger()
    assert store.menu_style == isolated_persistence.values['menu_style'] == 'ring'
    assert window.interaction_panel is None and satellite.interaction_panel is None
    satellite._show_context_menu(satellite.pos())
    assert satellite.interaction_panel.menu_style == 'ring'
    picker = next(button for button in satellite.interaction_panel.findChildren(QPushButton)
                  if button.property('menuStyle') == 'panel')
    QTest.mouseClick(picker, Qt.MouseButton.LeftButton)
    assert store.menu_style == isolated_persistence.values['menu_style'] == 'panel'
    assert window.interaction_panel is None and satellite.interaction_panel is None
    probe = QMenu()
    try:
        current = add_menu_style(probe, satellite)
        assert [a.data() for a in current.actions() if a.isChecked()] == ['panel']
    finally:
        probe.deleteLater()


@pytest.fixture
def cursor_model(qt_app, monkeypatch):
    import pet.simple_pet as module
    clock = SimpleNamespace(now=0., cursor=QPoint(230, 120))
    monkeypatch.setattr(module, 'QCursor', SimpleNamespace(pos=lambda: QPoint(clock.cursor)))
    monkeypatch.setattr(module, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(module, 'movement_bounds', lambda *_: QRect(0, 0, 761, 561))
    monkeypatch.setattr(module, 'available_rect', lambda *_: QRect(0, 0, 800, 600))
    pet = SimplePet('fox', personality_id='curious')
    pet.position, pet.window_size = QPoint(100, 100), QSize(40, 40)
    return pet, clock


def start_cursor_reaction(pet, clock):
    pet.tick_mouse_check()
    clock.now, clock.cursor = .2, QPoint(240, 120)
    pet.tick_mouse_check()


def test_cursor_uses_real_run_movement_and_finishes_without_stale_ownership(cursor_model):
    pet, clock = cursor_model
    start_cursor_reaction(pet, clock)
    assert pet.state == 'run' and pet._cursor_moving
    before = QPoint(pet.position)
    pet.get_next_position(.033)
    assert pet.position.x() > before.x() and pet.position.y() == before.y()
    for _ in range(40):
        pet.get_next_position(.033)
    assert pet.state == 'idle' and not pet._cursor_moving
    pet._start_random_walk()
    target = QPoint(pet._walk_target)
    pet.reset_cursor_reaction()
    assert pet._walk_target == target and pet.state == 'walk'


@pytest.mark.parametrize('busy', ['sleep', 'auto_sleep', 'ball', 'carry', 'petting'])
def test_cursor_respects_busy_states(cursor_model, busy):
    pet, clock = cursor_model
    if busy == 'sleep':
        pet.sleep()
    elif busy == 'auto_sleep':
        pet.change_state('lie')
    elif busy == 'ball':
        pet.chase(500, 200)
    elif busy == 'carry':
        pet._start_carry_ball()
    else:
        pet.pet_action()
    before = pet.state, pet._walk_target, pet.target_pos, pet.current_frame, pet.frame_counter
    start_cursor_reaction(pet, clock)
    assert before == (pet.state, pet._walk_target, pet.target_pos, pet.current_frame, pet.frame_counter)
    assert not pet._cursor_moving


def test_explicit_follow_overrides_calm_avoidance_and_stays_reachable(cursor_model):
    pet, clock = cursor_model
    pet.personality_id = 'calm'
    pet.set_follow_mouse(True)
    clock.cursor = QPoint(2000, 120)
    pet.tick_mouse_check()
    assert pet._walk_target.x() > pet.position.x()
    assert 0 <= pet._walk_target.x() <= 760
    assert not pet._cursor_moving


def test_explicit_follow_near_clamped_diagonal_does_not_start_empty_walk(cursor_model):
    pet, clock = cursor_model
    pet.position = QPoint(754, 554)
    pet.set_follow_mouse(True)
    clock.cursor = QPoint(2000, 2000)
    pet.tick_mouse_check()
    assert pet._walk_target is None and pet.state == 'idle'


def test_cursor_entering_dead_zone_stops_only_cursor_owned_movement(cursor_model):
    pet, clock = cursor_model
    start_cursor_reaction(pet, clock)
    clock.now, clock.cursor = .4, QPoint(150, 120)
    pet.tick_mouse_check()
    assert pet.state == 'idle' and pet._walk_target is None
    pet._start_random_walk()
    target = QPoint(pet._walk_target)
    clock.now = .6
    pet.tick_mouse_check()
    assert pet.state == 'walk' and pet._walk_target == target


def test_window_resyncs_cursor_during_menu_and_drag(window, cursor_model, monkeypatch):
    import ui.pet_window as module
    pet, clock = cursor_model
    monkeypatch.setattr(module, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(module, 'QCursor', SimpleNamespace(pos=lambda: QPoint(clock.cursor)))
    window._cursor_polled_at = None
    original = window.pet
    window.pet = pet
    try:
        start_cursor_reaction(pet, clock)
        window.dragging = True
        window._mouse_tick()
        assert pet.state == 'idle' and pet._walk_target is None
        clock.now, clock.cursor = .4, QPoint(260, 120)
        window.dragging = False
        window._mouse_tick()
        assert pet._walk_target is None
        window._show_context_menu(window.pos())
        clock.now, clock.cursor = .6, QPoint(250, 120)
        window._mouse_tick()
        window._close_interaction_panel()
        clock.now, clock.cursor = .8, QPoint(240, 120)
        window._mouse_tick()
        assert pet._walk_target is None
    finally:
        window._close_interaction_panel()
        window.pet = original
