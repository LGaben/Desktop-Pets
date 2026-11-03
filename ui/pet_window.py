# -*- coding: utf-8 -*-
"""Main transparent window that renders the desktop pet."""
from __future__ import annotations

import logging
from time import monotonic

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget,
)

from pet.ball import Ball
from pet.base_pet import BasePet
from pet.cursor_interest import CursorInterestCoordinator
from pet.factory import PetFactory
from pet.simple_pet import SimplePet
from pet.protocols import BallChaser, HasStats, MouseFollower
from ui.tray_manager import TrayManager
from utils.geometry import available_rect, clamp_position
from utils.i18n import t
from utils.settings_store import SettingsStore, store

_log = logging.getLogger(__name__)


class PetWindow(QWidget):
    """Frameless, transparent, always-on-top window that hosts the pet sprite.

    Pass manager=<primary_window> to create a satellite pet with no tray icon.
    """

    def __init__(
        self,
        manager: "PetWindow | None" = None,
        pet_type: str = "fox",
        name: str | None = None,
        settings_store: SettingsStore | None = None,
        restore: bool = False,
        record: dict | None = None,
    ) -> None:
        super().__init__()
        self._shutting_down = False
        self._disposed = False
        self._paused = True
        self._last_sprite_key = None
        self._last_tick = monotonic()
        self._manager = manager
        self.settings_store = manager.settings_store if manager else (settings_store or store)
        roster = self.settings_store.roster() if restore and manager is None else []
        record = record or (roster[0] if roster else {})
        pet_type = record.get("type", pet_type)
        name = record.get("name", name)
        self._restoring = True
        self._satellites: list[PetWindow] = []
        if manager is None:
            self._cursor_interest = CursorInterestCoordinator()
            self._cursor_polled_at = None
        self._hover_grace_until = 0.

        self.dragging = False
        self._press_global = None
        self.interaction_panel = None
        self.heart_overlay = None
        self.offset = QPoint()

        self.pet: BasePet = PetFactory.create(pet_type, name, personality_id=record.get('personality_id'))
        self.pet.set_state_saver(self.persist_state)
        self.ball = Ball()
        self.ball_widget = None
        self.throw_mode = False
        self.throw_start_pos: QPoint | None = None
        self.throw_current_pos: QPoint | None = None

        self._init_ui()
        self._init_timers()
        self._update_animation()
        if "position" in record:
            self.move(QPoint(*record["position"]))
        self._clamp_to_screen()
        self._resume()
        app = QApplication.instance()
        app.screenRemoved.connect(self._clamp_to_screen)
        app.screenAdded.connect(self._watch_screen)
        for screen in app.screens():
            self._watch_screen(screen)
        if self._is_primary:
            self.tray_manager = TrayManager(self)
            for saved in roster[1:]:
                satellite = PetWindow(manager=self, record=saved)
                self._satellites.append(satellite)
            self.tray_manager.rebuild_menu()
            app.aboutToQuit.connect(self._shutdown)
        self._restoring = False
        self.persist_state()

    @property
    def _is_primary(self) -> bool:
        return self._manager is None

    # -- setup ----------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(128, 128)

        self.sprite_label = QLabel(self)
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setMinimumSize(1, 1)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sprite_label)
        self.setLayout(layout)

        rect = available_rect(self._manager.pos() if self._manager else QPoint(0, 0))
        if self._is_primary:
            x = rect.right() - 200
        else:
            n = len(self._manager._satellites)
            x = max(rect.left() + 10, rect.right() - 200 - (n + 1) * 100)
        y = rect.bottom() - 200
        self.move(x, y)
        self.show()
        self.pet.position = QPoint(self.x(), self.y())

    def _init_timers(self) -> None:
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.setInterval(33)

        self._state_timer = QTimer(self)
        self._state_timer.timeout.connect(self._update_state)
        self._state_timer.setInterval(1000)

        self._behavior_timer = QTimer(self)
        self._behavior_timer.timeout.connect(self._update_behavior)
        self._behavior_timer.setInterval(3000)

        self._mouse_timer = QTimer(self)
        self._mouse_timer.timeout.connect(self._mouse_tick)
        self._mouse_timer.setInterval(200)

    # -- timer callbacks ------------------------------------------------------

    def _interaction_blocked(self) -> bool:
        return (self.dragging
                or self._press_global is not None
                or monotonic() < self._hover_grace_until
                or QApplication.activePopupWidget() is not None
                or bool(self.interaction_panel and self.interaction_panel.isVisible())
                or bool(self.ball_widget and self.ball_widget.grabbing))

    def _mouse_tick(self) -> None:
        if self._paused or self._disposed:
            return
        primary = self if self._is_primary else self._manager
        primary._update_cursor_interest()

    def _suspend_cursor_interest(self, now=None) -> None:
        primary = self if self._is_primary else self._manager
        primary._cursor_interest.release(self, monotonic() if now is None else now)
        if isinstance(self.pet, SimplePet):
            self.pet.reset_cursor_reaction()

    def _refresh_hover(self, now, cursor=None) -> None:
        cursor = QCursor.pos() if cursor is None else cursor
        if self.isVisible() and self.geometry().adjusted(-4, -4, 4, 4).contains(cursor):
            self._hover_grace_until = now + 1.8
            self._suspend_cursor_interest(now)
            if isinstance(self.pet, SimplePet):
                self.pet.hold_for_interaction()

    def _update_cursor_interest(self) -> None:
        now = monotonic()
        # Any visible window can poll, so hiding the primary does not stop the group.
        if self._cursor_polled_at is not None and now - self._cursor_polled_at < .15:
            return
        self._cursor_polled_at = now
        cursor = QCursor.pos()
        windows = [self] + self._satellites
        eligible = {}
        for window in windows:
            if window._disposed or window._paused or not window.isVisible():
                continue
            window._refresh_hover(now, cursor)
            pet = window.pet
            if isinstance(pet, SimplePet):
                if (not window._interaction_blocked() and not pet.following_mouse
                        and pet.state != 'lie' and not pet.is_chasing and not pet.carrying_ball
                        and not pet.petting and not (window.heart_overlay and window.heart_overlay.active)):
                    center = window.geometry().center()
                    eligible[window] = (center.x(), center.y())
                if pet.following_mouse and not window._interaction_blocked():
                    pet.tick_mouse_check()
        previous = self._cursor_interest.owner
        owner = self._cursor_interest.tick(
            now, (cursor.x(), cursor.y()), eligible,
            blocked=QApplication.activePopupWidget() is not None
            or any(window._press_global is not None or window.dragging for window in windows))
        if previous is not None and previous is not owner:
            previous.pet.reset_cursor_reaction()
        for window in windows:
            if isinstance(window.pet, SimplePet) and not window.pet.following_mouse:
                if window is owner:
                    window.pet.tick_mouse_check()
                else:
                    window.pet.reset_cursor_reaction(sampled_at=now)

    def _update_animation(self) -> None:
        now = monotonic()
        self._refresh_hover(now)
        dt = max(0.0, min(now - self._last_tick, 0.1))
        self._last_tick = now
        sprite = self.pet.get_current_sprite(dt)
        if sprite and sprite.cacheKey() != self._last_sprite_key:
            self._last_sprite_key = sprite.cacheKey()
            self.sprite_label.setPixmap(sprite)
            if self.size() != sprite.size():
                self.setFixedSize(sprite.size())
                self.pet.window_size = self.size()
                self._clamp_to_screen()
        if self.pet.is_moving and not self._interaction_blocked():
            self.move(self.pet.get_next_position(dt))
        if isinstance(self.pet, BallChaser) and self.pet.carrying_ball and self.ball_widget:
            self._hide_ball(cancel_chase=False)
        if self.heart_overlay and self.heart_overlay.active:
            if self.pet.pet_type != 'fox' or getattr(self.pet, 'petting', False):
                self.heart_overlay.tick(now)
            else:
                self._stop_hearts()

    def _update_state(self) -> None:
        self.pet.update_stats()

    def _update_behavior(self) -> None:
        if not self._interaction_blocked():
            self.pet.decide_next_action()

    # -- pet switching --------------------------------------------------------

    def set_pet_type(self, pet_type: str, name: str | None = None) -> None:
        """Replace the current pet with a new one of the given type."""
        self._suspend_cursor_interest()
        personality_id = getattr(self.pet, 'personality_id', None) if self.pet.pet_type == pet_type else None
        self._stop_hearts()
        self._close_interaction_panel()
        self._end_ball()
        self.pet.cleanup()
        self.pet.set_state_saver(None)
        if getattr(self, "settings_window", None):
            self.settings_window.close()
            self.settings_window.deleteLater()
            self.settings_window = None
        self.pet = PetFactory.create(pet_type, name, personality_id=personality_id)
        self.pet.set_state_saver(self.persist_state)
        self.pet.window_size = self.size()
        self._last_sprite_key = None
        self._last_tick = monotonic()
        if not self._paused:
            if isinstance(self.pet, HasStats):
                self._state_timer.start()
            else:
                self._state_timer.stop()
            if isinstance(self.pet, MouseFollower):
                self._mouse_timer.start()
            else:
                self._mouse_timer.stop()
        self.pet.position = QPoint(self.x(), self.y())
        self.ball = Ball()
        self.ball_widget = None
        self.throw_mode = False
        self.throw_start_pos = None
        self.throw_current_pos = None
        self.setToolTip("")

        if self._is_primary:
            self.tray_manager.update_tooltip(self.pet.name)
            self.tray_manager.rebuild_menu()
        self.persist_state()

    # -- multi-pet ------------------------------------------------------------

    def _add_satellite(self, pet_type: str) -> None:
        sat = PetWindow(manager=self, pet_type=pet_type)
        self._satellites.append(sat)
        self.tray_manager.rebuild_menu()
        self.persist_state(replace_corrupt=True)

    def _remove_self(self) -> None:
        if self._disposed:
            return
        self._dispose()
        if self._manager and self in self._manager._satellites:
            self._manager._satellites.remove(self)
            self._manager.tray_manager.rebuild_menu()
            self._manager.persist_state(replace_corrupt=True)
        self.close()
        self.deleteLater()

    def _cleanup_timers(self) -> None:
        for timer in (self._animation_timer, self._state_timer,
                      self._behavior_timer, self._mouse_timer):
            timer.stop()

    def _pause(self) -> None:
        if self._paused or not hasattr(self, "_animation_timer"):
            return
        self._paused = True
        self._suspend_cursor_interest()
        self._stop_hearts()
        self.dragging = False
        self._press_global = None
        self._close_interaction_panel()
        self._cleanup_timers()
        self._end_ball()
        self.pet.pause()
        self.persist_state()

    def _resume(self) -> None:
        if self._disposed or not hasattr(self, "_animation_timer"):
            return
        self._paused = False
        self._last_tick = monotonic()
        self.pet.resume()
        self._animation_timer.start()
        self._behavior_timer.start()
        if isinstance(self.pet, HasStats):
            self._state_timer.start()
        if isinstance(self.pet, MouseFollower):
            self._mouse_timer.start()

    def _dispose(self) -> None:
        if self._disposed:
            return
        self._pause()
        self._disposed = True
        self._end_ball()
        self.pet.cleanup()
        settings = getattr(self, "settings_window", None)
        if settings:
            settings.close()
            settings.deleteLater()
            self.settings_window = None
        self.pet.set_state_saver(None)

    def _watch_screen(self, screen) -> None:
        screen.availableGeometryChanged.connect(self._clamp_to_screen)
        self._clamp_to_screen()

    def _clamp_to_screen(self, *args) -> None:
        if self._disposed:
            return
        position = clamp_position(self.pos(), self.size(), available_rect(self.pos()))
        self.move(position)
        self.pet.position = position
        self.pet.window_size = self.size()

    def persist_state(self, replace_corrupt=False) -> None:
        primary = self if self._is_primary else self._manager
        if primary._restoring or primary._disposed or primary._shutting_down:
            return
        windows = [primary] + primary._satellites
        primary.settings_store.save(pets=[{
            "type": window.pet.pet_type, "name": window.pet.name,
            "position": [window.x(), window.y()],
            **({'personality_id': window.pet.personality_id} if getattr(window.pet, 'personality_id', None) else {}),
        } for window in windows if not window._disposed], replace_corrupt=replace_corrupt)
        if primary._is_primary and hasattr(primary, "tray_manager"):
            primary.tray_manager.update_tooltip(primary.pet.name)
            primary.tray_manager.rebuild_menu()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._resume()

    def hideEvent(self, event) -> None:
        self._pause()
        super().hideEvent(event)

    # -- tray -----------------------------------------------------------------

    def _toggle_all_visibility(self) -> None:
        any_visible = self.isVisible() or any(s.isVisible() for s in self._satellites)
        if any_visible:
            self.hide()
            for sat in self._satellites:
                sat.hide()
            self.tray_manager.set_toggle_text(False)
        else:
            self.show()
            self.raise_()
            for sat in self._satellites:
                sat.show()
                sat.raise_()
            self.tray_manager.set_toggle_text(True)
        self.tray_manager.rebuild_menu()

    def _toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
            if self._is_primary:
                self.tray_manager.set_toggle_text(False)
        else:
            self.show()
            self.raise_()
            if self._is_primary:
                self.tray_manager.set_toggle_text(True)

    # -- mouse events ---------------------------------------------------------

    def _pet_action(self) -> bool:
        if self._disposed or self._paused:
            return False
        if isinstance(self.pet, SimplePet) and self.heart_overlay and self.heart_overlay.active:
            return False
        accepted = self.pet.pet_action()
        if accepted and isinstance(self.pet, SimplePet):
            if self.heart_overlay is None:
                from ui.heart_overlay import HeartOverlay
                self.heart_overlay = HeartOverlay(self)
            self.heart_overlay.start(monotonic())
        return accepted

    def _stop_hearts(self) -> None:
        if self.heart_overlay:
            self.heart_overlay.stop()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._suspend_cursor_interest()
            if isinstance(self.pet, SimplePet):
                self.pet.hold_for_interaction()
            self.dragging = False
            self.offset = event.position().toPoint()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is not None and event.buttons() & Qt.MouseButton.LeftButton:
            distance = (event.globalPosition().toPoint() - self._press_global).manhattanLength()
            if not self.dragging and distance >= QApplication.startDragDistance():
                self.dragging = True
                self._stop_hearts()
                if cancel := getattr(self.pet, 'cancel_interaction', None):
                    cancel()
                if isinstance(self.pet, BallChaser):
                    self.pet.cancel_chase()
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.offset
            self.move(new_pos)
            self.pet.position = QPoint(new_pos.x(), new_pos.y())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._press_global is not None:
            was_dragging = (self.dragging
                            or (event.globalPosition().toPoint() - self._press_global).manhattanLength() >= QApplication.startDragDistance())
            self._press_global = None
            self.dragging = False
            self._clamp_to_screen()
            if was_dragging:
                self.persist_state()
            else:
                self._pet_action()

    # -- ball -----------------------------------------------------------------

    def _throw_ball(self, sx: int, sy: int, ex: int, ey: int) -> None:
        self._end_ball()
        self.pet.wake()
        self.ball.throw(sx, sy, ex, ey)
        if self.ball_widget is None:
            from ui.ball_widget import BallWidget
            self.ball_widget = BallWidget(self.ball, self)
        self.ball_widget.start()

    def on_ball_move(self, bx: float, by: float) -> None:
        """Called by BallWidget each physics frame."""
        if isinstance(self.pet, BallChaser):
            if getattr(self.pet, 'petting', False):
                return
            if self.pet.carrying_ball:
                self._hide_ball(cancel_chase=False)
                return
            self.pet.chase(bx, by)

    def on_ball_grab(self) -> None:
        self._stop_hearts()
        if cancel := getattr(self.pet, 'cancel_interaction', None):
            cancel()
        if isinstance(self.pet, BallChaser):
            self.pet.cancel_chase()

    def _hide_ball(self, cancel_chase=True) -> None:
        if self.ball_widget:
            self.ball_widget.hide()
            self.ball_widget.timer.stop()
        self.ball.active = False
        if cancel_chase and isinstance(self.pet, BallChaser):
            self.pet.cancel_chase()

    def _end_ball(self) -> None:
        self._hide_ball()
        if self.ball_widget:
            self.ball_widget.cleanup()
            self.ball_widget = None
        self.throw_mode = False
        self.throw_start_pos = self.throw_current_pos = None
        self.setToolTip("")

    def _sleep(self) -> None:
        self._stop_hearts()
        self._end_ball()
        self.pet.sleep()

    # -- context menu ---------------------------------------------------------

    def _close_interaction_panel(self) -> None:
        if self.interaction_panel:
            self.interaction_panel.close()
            self.interaction_panel.deleteLater()
            self.interaction_panel = None

    def _show_context_menu(self, pos: QPoint) -> None:
        from ui.interaction_panel import InteractionPanel
        self._close_interaction_panel()
        self._suspend_cursor_interest()
        character = getattr(self.pet, 'personality_id', None)
        loader = getattr(self.pet, 'sprite_loader', None)
        portraits = loader.get_animation('idle') if loader is not None else []
        portrait = portraits[0] if portraits else self.sprite_label.pixmap()
        self.interaction_panel = InteractionPanel(
            self, self.pet.name, t(f'personality_{character}') if character else '',
            self._interaction_actions(pos), style=self.settings_store.menu_style,
            portrait=portrait, style_changed=self._set_menu_style)
        self.interaction_panel.open_at(pos)

    def _interaction_actions(self, pos=None):
        state = getattr(self.pet, 'state', None)
        state = state.value if hasattr(state, 'value') else state
        sleeping = state in ('lie', 'sleep')
        actions = [(t('pet_action'), self._pet_action)]
        if isinstance(self.pet, BallChaser):
            actions.append((t('ball_action'), self._enter_throw_mode))
        actions.append((t('wake_up') if sleeping else t('sleep'), self.pet.wake if sleeping else self._sleep))
        if isinstance(self.pet, MouseFollower):
            actions.append((t('stop_follow') if self.pet.following_mouse else t('start_follow'), self._toggle_follow_mouse))
        actions.append((t('settings'), self._show_settings))
        if self._is_primary:
            actions += [(t('hide_to_tray'), self._toggle_visibility), (t('quit'), self._quit)]
        else:
            actions.append((t('remove_pet'), self._remove_self))
        return actions

    def _activate_tray_action(self, callback):
        if self._disposed:
            return
        if not self.isVisible():
            self.show()
        self._hover_grace_until = monotonic() + 1.8
        self._suspend_cursor_interest()
        callback()

    # -- menu actions ---------------------------------------------------------

    def _set_menu_style(self, style: str) -> None:
        from utils.settings_store import MENU_STYLES
        if style not in MENU_STYLES:
            return
        primary = self if self._is_primary else self._manager
        for window in [primary] + primary._satellites:
            window._close_interaction_panel()
        primary.settings_store.save(menu_style=style)
        primary.tray_manager.rebuild_menu()

    def _toggle_follow_mouse(self) -> None:
        if not isinstance(self.pet, MouseFollower):
            return
        self.pet.set_follow_mouse(not self.pet.following_mouse)

    def _enter_throw_mode(self) -> None:
        self._end_ball()
        self.pet.wake()
        from ui.ball_widget import BallWidget
        bounds = available_rect(self.pos())
        size = QSize(32, 32)
        point = self.pos() + QPoint(self.width() + 8, (self.height() - 32) // 2)
        if not bounds.contains(QRect(point, size)):
            point = self.pos() + QPoint(-40, (self.height() - 32) // 2)
        point = clamp_position(point, size, bounds)
        self.ball.x, self.ball.y = point.x() + 16, point.y() + 16
        self.ball.active = False
        self.ball_widget = BallWidget(self.ball, self)
        self.ball_widget.start()

    def _show_settings(self) -> None:
        from ui.settings import SettingsWindow
        if getattr(self, "settings_window", None) and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        if getattr(self, "settings_window", None):
            self.settings_window.deleteLater()
        self.settings_window = SettingsWindow(self.pet, self)
        self.settings_window.show()

    def _shutdown(self) -> None:
        if self._disposed:
            return
        self.persist_state()
        self._shutting_down = True
        self.pet.save_state()
        for sat in list(self._satellites):
            sat._dispose()
            sat.close()
            sat.deleteLater()
        self._satellites.clear()
        self._dispose()
        self.hide()
        self.tray_manager.tray.hide()

    def _quit(self) -> None:
        self._shutdown()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        if self._disposed:
            event.accept()
        elif not self._is_primary:
            self._remove_self()
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray_manager.set_toggle_text(False)
            self.tray_manager.show_hidden_message()
