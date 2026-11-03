"""Group scheduling and reliable menu access on real Qt windows."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QPushButton

from tests.test_cursor_interest import ChoiceRng
from utils.i18n import t


@pytest.fixture
def group(window, monkeypatch):
    import ui.pet_window as window_module
    import pet.simple_pet as pet_module
    clock = SimpleNamespace(now=0., cursor=QPoint(210, 160))
    cursor = SimpleNamespace(pos=lambda: QPoint(clock.cursor))
    monkeypatch.setattr(window_module, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(pet_module, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(window_module, 'QCursor', cursor)
    monkeypatch.setattr(pet_module, 'QCursor', cursor)
    window._add_satellite('fox')
    satellite = window._satellites[0]
    for index, item in enumerate((window, satellite)):
        item.move(100, 100 + index * 100)
        item.pet.position = QPoint(item.pos())
        item.pet.personality_id = 'curious'
        item.pet.cancel_chase()
        item._hover_grace_until = 0.
    window._cursor_interest.rng = ChoiceRng()
    window._cursor_polled_at = None
    return window, satellite, clock


def grant(primary, satellite, clock):
    for index in range(4):
        clock.now, clock.cursor = index * .2, QPoint(210 + index * 5, 160)
        (primary if index % 2 else satellite)._mouse_tick()
    assert primary._cursor_interest.owner is satellite


def test_only_selected_pet_moves_and_duplicate_polls_do_not_reroll(group):
    primary, satellite, clock = group
    grant(primary, satellite, clock)
    assert satellite.pet._cursor_moving
    assert not primary.pet._cursor_moving
    calls = len(primary._cursor_interest.rng.choices)
    deadline = primary._cursor_interest.expires
    primary._mouse_tick()
    satellite._mouse_tick()
    assert len(primary._cursor_interest.rng.choices) == calls
    assert primary._cursor_interest.expires == deadline
    for index in range(4, 21):
        clock.now, clock.cursor = index * .2, QPoint(215 + index % 2 * 6, 160)
        satellite._mouse_tick()
    assert primary._cursor_interest.owner is None
    assert not satellite.pet._cursor_moving
    assert len(primary._cursor_interest.rng.choices) == calls


def test_hidden_primary_does_not_stop_visible_satellite_polling(group):
    primary, satellite, clock = group
    grant(primary, satellite, clock)
    primary.hide()
    clock.now, clock.cursor = .8, QPoint(230, 160)
    satellite._mouse_tick()
    assert primary._cursor_interest.owner is satellite
    assert satellite._mouse_timer.isActive() and not primary._mouse_timer.isActive()
    satellite.hide()
    assert primary._cursor_interest.owner is None
    assert not satellite._mouse_timer.isActive()
    sampled = primary._cursor_polled_at
    clock.now = 20.
    primary._mouse_tick()
    satellite._mouse_tick()
    assert primary._cursor_polled_at == sampled


@pytest.mark.parametrize('action', ['hide', 'remove', 'retype'])
def test_owner_lifecycle_releases_episode_immediately(group, action):
    primary, satellite, clock = group
    grant(primary, satellite, clock)
    if action == 'hide':
        satellite.hide()
    elif action == 'remove':
        satellite._remove_self()
    else:
        satellite.set_pet_type('panda')
    assert primary._cursor_interest.owner is None
    assert primary._cursor_interest.cooldown_until >= clock.now + 4
    assert not satellite.pet._cursor_moving


def test_animation_tick_hover_stops_free_walk_and_gives_click_grace(group, monkeypatch):
    primary, satellite, clock = group
    pet = primary.pet
    pet._walk_target, pet._walk_timer = QPoint(500, 100), 80
    pet.change_state('walk')
    primary._cursor_interest.owner = primary
    primary._cursor_interest.expires = 3.
    clock.cursor = primary.geometry().center()
    before = QPoint(primary.pos())
    primary._update_animation()
    assert primary.pos() == before and pet.state == 'idle'
    assert pet._walk_target is None
    assert primary._cursor_interest.owner is None
    assert primary._hover_grace_until == 1.8
    clock.cursor, clock.now = QPoint(700, 550), 1.
    decide = Mock()
    monkeypatch.setattr(pet, 'decide_next_action', decide)
    primary._update_behavior()
    decide.assert_not_called()
    clock.now = 2.
    primary._update_behavior()
    decide.assert_called_once()


@pytest.mark.parametrize('activity', ['ball', 'carry', 'follow'])
def test_hover_freezes_without_losing_explicit_activity(group, activity):
    primary, satellite, clock = group
    pet = primary.pet
    if activity == 'ball':
        pet.chase(500, 100)
    elif activity == 'carry':
        pet._start_carry_ball()
    else:
        pet.set_follow_mouse(True)
        pet.tick_mouse_check()
    target, carry_timer = pet.target_pos, pet._carry_timer
    before = QPoint(primary.pos())
    clock.cursor = primary.geometry().center()
    primary._update_animation()
    assert primary.pos() == before
    assert pet.target_pos == target and pet._carry_timer == carry_timer
    assert pet.is_chasing == (activity == 'ball')
    assert pet.carrying_ball == (activity == 'carry')
    assert pet.following_mouse == (activity == 'follow')


def test_press_freezes_immediately_before_drag_threshold_and_release_pets(group):
    primary, satellite, clock = group
    clock.cursor = QPoint(700, 550)
    primary.pet._walk_target, primary.pet._walk_timer = QPoint(500, 300), 80
    primary.pet.change_state('walk')
    point = primary.rect().center()
    QTest.mousePress(primary, Qt.MouseButton.LeftButton, pos=point)
    assert primary._interaction_blocked() and not primary.dragging
    before = QPoint(primary.pos())
    clock.now = .1
    primary._update_animation()
    assert primary.pos() == before
    QTest.mouseRelease(primary, Qt.MouseButton.LeftButton, pos=point)
    assert primary.pet.petting and primary._press_global is None


@pytest.mark.parametrize('style', ['panel', 'ring'])
def test_settings_shortcut_calls_shared_action_directly(group, monkeypatch, style):
    primary, satellite, clock = group
    callback = Mock()
    monkeypatch.setattr(primary, '_show_settings', callback)
    primary.settings_store.menu_style = style
    primary._show_context_menu(primary.pos())
    shortcut = next(button for button in primary.interaction_panel.findChildren(QPushButton)
                    if button.accessibleName() == t('settings'))
    assert shortcut.accessibleName() == t('settings') and shortcut.minimumHeight() >= 44
    QTest.mouseClick(shortcut, Qt.MouseButton.LeftButton)
    callback.assert_called_once()


def test_tray_reaches_each_pet_without_hitting_its_sprite(group, monkeypatch):
    primary, satellite, clock = group
    callback = Mock()
    monkeypatch.setattr(satellite, '_show_settings', callback)
    satellite.hide()
    primary.tray_manager.rebuild_menu()
    menu = primary.tray_manager.tray.contextMenu()
    pets = next(action.menu() for action in menu.actions() if action.text() == t('pets_actions'))
    assert len(pets.actions()) == 2
    second = pets.actions()[1].menu()
    next(action for action in second.actions() if action.text() == t('settings')).trigger()
    callback.assert_called_once()
    assert satellite.isVisible() and satellite._hover_grace_until == clock.now + 1.8


def test_nonfox_hearts_exclude_automatic_interest(group):
    primary, satellite, clock = group
    satellite.set_pet_type('panda')
    assert satellite._pet_action()
    assert satellite.heart_overlay.active and not satellite.pet.petting
    for index in range(4):
        clock.now, clock.cursor = index * .2, QPoint(210 + index * 5, 160)
        primary._mouse_tick()
    assert primary._cursor_interest.owner is primary
    assert not satellite.pet._cursor_moving
