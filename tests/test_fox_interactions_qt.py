"""Actual Qt event/lifecycle checks; require an available PyQt6 runtime."""
import pytest

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QImage, QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from pet.simple_pet import SimplePet
from pet.catalog import PET_TYPES
from utils.i18n import t
from utils.paths import resource_base


@pytest.mark.parametrize('pet_type', PET_TYPES[1:])
def test_other_pets_accept_hearts_without_changing_behavior(qt_app, pet_type):
    pet = SimplePet(pet_type)
    pet.chase(400, 300)
    pet._follow_mouse = True
    pet.current_frame, pet.frame_counter = 2, 3.5
    before = vars(pet).copy()
    reaction_before = vars(pet._pet_reaction).copy()
    assert pet.pet_action() is True
    assert vars(pet) == before
    assert vars(pet._pet_reaction) == reaction_before
    assert not pet.petting
    pet.sleep()
    before = vars(pet).copy()
    assert pet.pet_action() is False
    assert vars(pet) == before


@pytest.mark.parametrize('facing_right', [False, True])
@pytest.mark.parametrize('via_panel', [False, True])
def test_other_pet_hearts_click_panel_clock_and_lifecycle(window, monkeypatch,
                                                         facing_right, via_panel):
    import ui.pet_window as window_module
    import ui.heart_overlay as overlay_module
    from ui.heart_effect import DURATION, WIDTH
    monkeypatch.setattr(overlay_module, 'available_rect', lambda point: QRect(0, 0, 2000, 1200))
    window.set_pet_type('snake')
    window.move(500, 400)
    window.pet.facing_right = facing_right
    if via_panel:
        window._show_context_menu(window.pos())
        button = next(button for button in window.interaction_panel.findChildren(QPushButton)
                      if button.text() == t('pet_action'))
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    else:
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=window.rect().center())
    overlay = window.heart_overlay
    assert overlay.active and not window.pet.petting
    assert overlay.x() == window.x() + window.width() // 2 - WIDTH // 2
    started = overlay.started
    assert window._pet_action() is False
    assert overlay.started == started
    monkeypatch.setattr(window_module, 'monotonic', lambda: started + .3)
    window._update_animation()
    assert overlay.active and overlay.elapsed == pytest.approx(.3)
    monkeypatch.setattr(window_module, 'monotonic', lambda: started + DURATION + .01)
    window._update_animation()
    assert not overlay.active
    for stop in (window.hide, window._sleep, lambda: window.set_pet_type('panda'),
                 window._dispose):
        window.show()
        window.pet.wake()
        assert window._pet_action()
        stop()
        assert not overlay.active


def test_click_pets_but_threshold_drag_does_not(window):
    window.pet.change_state('idle')
    point = window.rect().center()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
    assert window.pet.petting
    window.pet.cancel_interaction()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=point)
    destination = point + QPoint(QApplication.startDragDistance() + 8, 0)
    event = QMouseEvent(QEvent.Type.MouseMove, QPointF(destination), QPointF(window.mapToGlobal(destination)),
                        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, event)
    assert window.dragging
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=destination)
    assert not window.pet.petting
    assert not window.heart_overlay.active


def test_head_reaction_preserves_idle_phase_and_user_sleep(qt_app):
    pet = SimplePet('fox', personality_id='calm')
    pet.current_frame, pet.frame_counter = 3, 2
    pet.pet_action()
    assert (pet.current_frame, pet.frame_counter) == (3, 2)
    for _ in range(40):
        sprite = pet.get_current_sprite(.033)
        assert (sprite.width(), sprite.height()) == (46, 37)
    assert not pet.petting
    pet.sleep()
    pet.pet_action()
    pet.chase(100, 100)
    pet.decide_next_action()
    assert pet.state == 'lie' and not pet.petting and not pet.is_chasing


def test_panel_clamps_and_closes_on_escape_hide_and_switch(window, monkeypatch):
    import ui.interaction_panel as module
    bounds = QRect(-900, -600, 800, 600)
    monkeypatch.setattr(module, 'available_rect', lambda point: bounds)
    window._show_context_menu(QPoint(-110, -10))
    panel = window.interaction_panel
    assert bounds.contains(panel.geometry())
    assert any(button.text() == t('pet_action') for button in panel.findChildren(QPushButton))
    QTest.keyClick(panel, Qt.Key.Key_Escape)
    assert not panel.isVisible()
    window._show_context_menu(window.pos())
    window.hide()
    assert window.interaction_panel is None
    window.show()
    window._show_context_menu(window.pos())
    window.set_pet_type('panda')
    assert window.interaction_panel is None


def test_ball_no_move_release_no_jump_cancel_and_resting_catch(window):
    window._enter_throw_mode()
    widget = window.ball_widget
    center = widget.rect().center()
    original = window.ball.x, window.ball.y
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=center)
    assert widget.grabbing and not window.pet.is_chasing
    window._mouse_tick()
    assert not window.pet.is_chasing and window.pet._walk_target is None
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=center)
    assert (window.ball.x, window.ball.y) == original
    assert window.ball.active and not widget.grabbing
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=center)
    QTest.keyClick(widget, Qt.Key.Key_Escape)
    assert not widget.grabbing and QWidget.mouseGrabber() is not widget
    assert not window.pet.is_chasing
    widget.timer.stop()
    window.ball.active = False
    window.pet.chase(window.ball.x, window.ball.y)
    window.pet.stop_chase()
    window._update_animation()
    assert not widget.isVisible()


def test_character_survives_settings_language_and_roster(window):
    chosen = window.pet.personality_id
    window._show_settings()
    window.settings_window._set_language('en')
    window.settings_window._apply()
    assert window.pet.personality_id == chosen
    window.persist_state()
    assert window.settings_store.roster()[0]['personality_id'] == chosen


def test_every_phase_head_and_mirror_uses_real_pose_assets(qt_app):
    pet = SimplePet('fox', personality_id='active')
    for mirrored in (False, True):
        pet.facing_right = not mirrored
        for head, age in ((0, None), (1, .2), (2, .5)):
            for phase in range(5):
                pet.current_frame = phase
                pet.frame_counter = 0
                pet._pet_reaction.elapsed = age
                actual = pet.get_current_sprite(0).toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                path = resource_base() / f'assets/sprites/fox/pet_react/head_{head}/frame_{phase + 1}.png'
                expected = QImage(str(path))
                if mirrored:
                    expected = expected.mirrored(True, False)
                assert actual == expected.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)


def test_ball_spawn_at_negative_screen_edge_is_contained_and_beside_pet(window, monkeypatch):
    import ui.pet_window as module
    bounds = QRect(-500, -300, 500, 300)
    monkeypatch.setattr(module, 'available_rect', lambda point: bounds)
    window.move(-window.width() - 1, -window.height() - 1)
    window._enter_throw_mode()
    assert bounds.contains(window.ball_widget.geometry())
    assert not window.geometry().intersects(window.ball_widget.geometry())


def test_unexpected_ball_ungrab_cancels_session(window):
    window._enter_throw_mode()
    widget = window.ball_widget
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=widget.rect().center())
    QApplication.sendEvent(widget, QEvent(QEvent.Type.UngrabMouse))
    assert not widget.grabbing and not window.ball.active
    assert QWidget.mouseGrabber() is not widget


def test_hearts_for_accepted_petting_and_reuse_overlay(window):
    from PyQt6.QtCore import QTimer
    from ui.heart_effect import DURATION
    before = window.size(), window.pos(), window.pet.current_frame, window.pet.frame_counter
    assert window._pet_action() is True
    overlay = window.heart_overlay
    assert overlay.active and overlay.isVisible()
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput
    assert overlay.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    assert overlay.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert not overlay.findChildren(QTimer)
    assert before == (window.size(), window.pos(), window.pet.current_frame, window.pet.frame_counter)
    started = overlay.started
    assert window._pet_action() is False
    assert window.heart_overlay is overlay and overlay.started == started
    overlay.tick(started + DURATION + .01)
    assert not overlay.active and not overlay.isVisible()
    window.pet.cancel_interaction()
    window._sleep()
    assert window._pet_action() is False
    window.set_pet_type('panda')
    assert not overlay.active
    assert window._pet_action() is True
    assert overlay.active and not window.pet.petting


def test_panel_pet_button_starts_hearts_and_lifecycle_clears_them(window):
    window._show_context_menu(window.pos())
    button = next(button for button in window.interaction_panel.findChildren(QPushButton)
                  if button.text() == t('pet_action'))
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert window.heart_overlay.active
    window.hide()
    assert not window.heart_overlay.active
    window.show()
    assert window._pet_action()
    window._sleep()
    assert not window.heart_overlay.active
    window.pet.wake()
    assert window._pet_action()
    window.set_pet_type('panda')
    assert not window.heart_overlay.active


def test_hearts_follow_pet_and_clamp_to_negative_screen(window, monkeypatch):
    import ui.heart_overlay as module
    bounds = QRect(-500, -300, 500, 300)
    monkeypatch.setattr(module, 'available_rect', lambda point: bounds)
    window.move(-window.width() - 1, -299)
    assert window._pet_action()
    overlay = window.heart_overlay
    assert bounds.contains(overlay.geometry())
    window.move(-300, -100)
    overlay.tick(overlay.started + .3)
    assert bounds.contains(overlay.geometry())
    assert overlay.x() < -200
    window._dispose()
    assert not overlay.active and not overlay.isVisible()
