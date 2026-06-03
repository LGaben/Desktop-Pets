# -*- coding: utf-8 -*-
"""Main transparent window that renders the desktop pet."""
from __future__ import annotations

import logging

from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtWidgets import (
    QAction, QApplication, QLabel, QMenu, QVBoxLayout, QWidget,
)

from pet.base_pet import BasePet
from pet.ball import Ball
from pet.factory import PetFactory
from pet.protocols import BallChaser, MouseFollower
from ui.tray_manager import TrayManager
from utils.i18n import t

_log = logging.getLogger(__name__)

_PET_EMOJI: dict[str, str] = {
    "fox":        "🦊",
    "panda":      "🐼",
    "cockatiel":  "🐦",
    "dog":        "🐕",
    "turtle":     "🐢",
    "totoro":     "🐻",
    "chicken":    "🐔",
    "clippy":     "📎",
    "crab":       "🦀",
    "deno":       "🦕",
    "horse":      "🐴",
    "mod":        "🔮",
    "monkey":     "🐒",
    "morph":      "💜",
    "rat":        "🐀",
    "rocky":      "🪨",
    "rubber_duck":"🦆",
    "skeleton":   "💀",
    "snail":      "🐌",
    "snake":      "🐍",
    "zappy":      "⚡",
}


class PetWindow(QWidget):
    """Frameless, transparent, always-on-top window that hosts the pet sprite.

    Pass manager=<primary_window> to create a satellite pet with no tray icon.
    """

    def __init__(
        self,
        manager: "PetWindow | None" = None,
        pet_type: str = "fox",
        name: str | None = None,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._satellites: list[PetWindow] = []

        self.dragging = False
        self.offset = QPoint()

        self.pet: BasePet = PetFactory.create(pet_type, name)
        self.ball = Ball()
        self.ball_widget = None
        self.throw_mode = False
        self.throw_start_pos: QPoint | None = None
        self.throw_current_pos: QPoint | None = None

        self._init_ui()
        self._init_timers()
        if self._is_primary:
            self.tray_manager = TrayManager(self)

    @property
    def _is_primary(self) -> bool:
        return self._manager is None

    # -- setup ----------------------------------------------------------------

    def _init_ui(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(128, 128)

        self.sprite_label = QLabel(self)
        self.sprite_label.setAlignment(Qt.AlignCenter)
        self.sprite_label.setMinimumSize(64, 64)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sprite_label)
        self.setLayout(layout)

        rect = QApplication.desktop().availableGeometry()
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
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.start(33)

        self._state_timer = QTimer()
        self._state_timer.timeout.connect(self._update_state)
        self._state_timer.start(1000)

        self._behavior_timer = QTimer()
        self._behavior_timer.timeout.connect(self._update_behavior)
        self._behavior_timer.start(3000)

        self._mouse_timer = QTimer()
        self._mouse_timer.timeout.connect(self._mouse_tick)
        self._mouse_timer.start(200)


    # -- timer callbacks ------------------------------------------------------

    def _mouse_tick(self) -> None:
        if isinstance(self.pet, MouseFollower):
            self.pet.tick_mouse_check()

    def _update_animation(self) -> None:
        sprite = self.pet.get_current_sprite()
        if sprite:
            self.sprite_label.setPixmap(sprite)
            self.sprite_label.resize(sprite.size())
            self.resize(sprite.size())
        if self.pet.is_moving and not self.dragging:
            new_pos = self.pet.get_next_position()
            self.move(new_pos.x(), new_pos.y())

    def _update_state(self) -> None:
        self.pet.update_stats()

    def _update_behavior(self) -> None:
        self.pet.decide_next_action()

    # -- pet switching --------------------------------------------------------

    def set_pet_type(self, pet_type: str, name: str | None = None) -> None:
        """Replace the current pet with a new one of the given type."""
        self.pet = PetFactory.create(pet_type, name)
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

    # -- multi-pet ------------------------------------------------------------

    def _add_satellite(self, pet_type: str) -> None:
        sat = PetWindow(manager=self, pet_type=pet_type)
        self._satellites.append(sat)
        self.tray_manager.rebuild_menu()

    def _remove_self(self) -> None:
        if hasattr(self, "settings_window") and self.settings_window:
            self.settings_window.close()
        if self._manager and self in self._manager._satellites:
            self._manager._satellites.remove(self)
            self._manager.tray_manager.rebuild_menu()
        self._cleanup_timers()
        self.close()

    def _cleanup_timers(self) -> None:
        self._animation_timer.stop()
        self._state_timer.stop()
        self._behavior_timer.stop()
        self._mouse_timer.stop()

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

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            if self.throw_mode:
                self.throw_start_pos = event.globalPos()
                self.throw_current_pos = event.globalPos()
                return
            self.dragging = True
            self.offset = event.pos()
        elif event.button() == Qt.RightButton:
            if self.throw_mode:
                self.throw_mode = False
                self.setToolTip("")
                return
            self._show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event) -> None:
        if self.throw_mode and self.throw_start_pos:
            self.throw_current_pos = event.globalPos()
            dx = self.throw_current_pos.x() - self.throw_start_pos.x()
            dy = self.throw_current_pos.y() - self.throw_start_pos.y()
            self.setToolTip(
                f"🎾 Бросок: ({dx}, {dy})  скорость: {int((dx * dx + dy * dy) ** 0.5)}\n"
                "Отпустите ЛКМ чтобы кинуть"
            )
            return
        if self.dragging and event.buttons() == Qt.LeftButton:
            new_pos = self.mapToGlobal(event.pos() - self.offset)
            self.move(new_pos)
            self.pet.position = QPoint(new_pos.x(), new_pos.y())

    def mouseReleaseEvent(self, event) -> None:
        if (
            event.button() == Qt.LeftButton
            and self.throw_mode
            and self.throw_start_pos
        ):
            end = event.globalPos()
            self._throw_ball(
                self.throw_start_pos.x(), self.throw_start_pos.y(),
                end.x(), end.y(),
            )
            self.throw_mode = False
            self.throw_start_pos = None
            self.throw_current_pos = None
            self.setToolTip("")
            return
        if event.button() == Qt.LeftButton:
            self.dragging = False

    # -- ball -----------------------------------------------------------------

    def _throw_ball(self, sx: int, sy: int, ex: int, ey: int) -> None:
        self.ball.throw(sx, sy, ex, ey)
        if self.ball_widget is None:
            from ui.ball_widget import BallWidget
            self.ball_widget = BallWidget(self.ball, self)
        self.ball_widget.show()
        self.ball_widget.timer.start(16)

    def on_ball_move(self, bx: float, by: float) -> None:
        """Called by BallWidget each physics frame."""
        if isinstance(self.pet, BallChaser):
            if self.pet._carrying_ball:
                self._hide_ball()
                return
            self.pet.chase(bx, by)

    def _hide_ball(self) -> None:
        if self.ball_widget:
            self.ball_widget.hide()
            self.ball_widget.timer.stop()
        self.ball.active = False

    # -- context menu ---------------------------------------------------------

    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(50,50,50,230);
                color: white;
                border: 1px solid gray;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item { padding: 8px 20px; border-radius: 3px; }
            QMenu::item:selected { background-color: rgba(70,130,180,200); }
        """)

        emoji = _PET_EMOJI.get(self.pet.pet_type, "🐾")
        info = QAction(f"{emoji} {self.pet.name}  (Ур. {self.pet.level})", self)
        info.setEnabled(False)
        menu.addAction(info)

        menu.addSeparator()

        # Sleep / wake toggle — handle both SimplePet str state and FullPet PetState enum
        _state = getattr(self.pet, "state", None)
        _sval  = _state.value if hasattr(_state, "value") else _state
        is_sleeping = _sval in ("lie", "sleep")
        if is_sleeping:
            wake = QAction(t("wake_up"), self)
            wake.triggered.connect(self.pet.wake)
            menu.addAction(wake)
        else:
            sleep = QAction(t("sleep"), self)
            sleep.triggered.connect(self.pet.sleep)
            menu.addAction(sleep)

        # Ball throw
        if isinstance(self.pet, BallChaser):
            ball = QAction(t("throw_ball"), self)
            ball.triggered.connect(self._enter_throw_mode)
            menu.addAction(ball)

        # Mouse-follow toggle
        if isinstance(self.pet, MouseFollower):
            is_following = self.pet._follow_mouse
            label = t("stop_follow") if is_following else t("start_follow")
            follow = QAction(label, self)
            follow.triggered.connect(self._toggle_follow_mouse)
            menu.addAction(follow)

        menu.addSeparator()

        settings = QAction(t("settings"), self)
        settings.triggered.connect(self._show_settings)
        menu.addAction(settings)

        if self._is_primary:
            hide_action = QAction(t("hide_to_tray"), self)
            hide_action.triggered.connect(self._toggle_visibility)
            menu.addAction(hide_action)

            menu.addSeparator()

            quit_a = QAction(t("quit"), self)
            quit_a.triggered.connect(self._quit)
            menu.addAction(quit_a)
        else:
            menu.addSeparator()

            remove_a = QAction(t("remove_pet"), self)
            remove_a.triggered.connect(self._remove_self)
            menu.addAction(remove_a)

        menu.exec_(pos)

    # -- menu actions ---------------------------------------------------------

    def _toggle_follow_mouse(self) -> None:
        if not isinstance(self.pet, MouseFollower):
            return
        self.pet._follow_mouse = not self.pet._follow_mouse
        if self.pet._follow_mouse:
            self.pet._walk_target = None
        else:
            self.pet._walk_target = None
            self.pet.change_state("idle")

    def _enter_throw_mode(self) -> None:
        self.throw_mode = True
        self.throw_start_pos = None
        self.throw_current_pos = None
        self.setToolTip(
            "🎾 Нажмите ЛКМ и перетащите чтобы задать направление броска"
        )

    def _show_settings(self) -> None:
        from ui.settings import SettingsWindow
        if hasattr(self, "settings_window") and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = SettingsWindow(self.pet, self)
        self.settings_window.show()

    def _quit(self) -> None:
        self.pet.save_state()
        for sat in list(self._satellites):
            sat._cleanup_timers()
        self._cleanup_timers()
        self.tray_manager.tray.hide()
        QApplication.quit()

    # -- window events --------------------------------------------------------

    def closeEvent(self, event) -> None:
        if not self._is_primary:
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray_manager.set_toggle_text(False)
        self.tray_manager.show_hidden_message()
