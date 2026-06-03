# -*- coding: utf-8 -*-
"""Simplified pet (no stats) that chases balls and follows the mouse."""
from __future__ import annotations

import math
import random

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QCursor, QPixmap, QTransform
from PyQt5.QtWidgets import QApplication

from pet.base_pet import BasePet
from utils.i18n import t
from utils.sprite_loader import SpriteLoader

_SIMPLE_PET_ANIMATIONS = ["idle", "walk", "run", "with_ball", "lie"]


class SimplePet(BasePet):
    """Lightweight pet driven purely by physics and mouse-tracking.

    No hunger/energy/happiness stats — just animation, movement,
    ball-chasing, and optional cursor-following.

    Args:
        pet_type: One of ``"fox"``, ``"panda"``, or ``"cockatiel"``.
        name: Display name override; falls back to the type default.
    """

    def __init__(self, pet_type: str = "fox", name: str | None = None) -> None:
        self.pet_type = pet_type
        self.name = name or t(f"name_{pet_type}")
        self.level: int = 1

        self.state = "idle"
        self.is_moving = False
        self.facing_right = True
        self.position = QPoint(100, 100)
        self.velocity = QPoint(0, 0)

        self.is_chasing = False
        self.target_pos: QPoint | None = None
        self._carrying_ball = False
        self._carry_timer = 0

        self.sprite_loader = SpriteLoader(pet_type, _SIMPLE_PET_ANIMATIONS)
        self.current_frame = 0
        self.animation_speed = 5
        self.frame_counter = 0
        self._anim_cycle = 80 if pet_type == "panda" else 40

        self._walk_target: QPoint | None = None
        self._walk_timer = 0
        self._mouse_check_counter = 0
        self._follow_mouse = False
        self._spontaneous_counter = random.randint(4500, 18000)
        self._mouse_last_pos = QCursor.pos()
        self._mouse_still_counter = 0
        self._follow_idle_still_threshold = random.randint(25, 75)
        self._in_idle_behavior = False
        self._user_sleep = False
        self._lie_timer = 0
        self._auto_sleep_duration = 0

    # -- BasePet interface ----------------------------------------------------

    def update_stats(self) -> None:
        """No-op: SimplePet has no quantified stats."""

    def check_critical_states(self) -> None:
        """No-op: SimplePet has no critical stat thresholds."""

    def decide_next_action(self) -> None:
        """Randomly walk or lie down when not already occupied."""
        if self.is_chasing or self._carrying_ball:
            self._lie_timer = 0
            return
        if self.state == "lie":
            if not self._user_sleep:
                self._lie_timer += 1
                if self._lie_timer >= self._auto_sleep_duration:
                    self._lie_timer = 0
                    self.wake()
            return
        self._lie_timer = 0
        if self._walk_target is not None:
            return
        if self._follow_mouse:
            self._follow_mouse_tick()
            return
        r = random.random()
        if r < 0.45:
            self._start_random_walk()
        elif r < 0.55:
            self.change_state("lie")

    def get_current_sprite(self) -> QPixmap | None:
        """Return the current animation frame, mirrored when facing left."""
        sprites = self.sprite_loader.get_animation(self.state)
        if not sprites:
            return None
        speed = self._calc_anim_speed(len(sprites))
        self.frame_counter += 1
        if self.frame_counter >= speed:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(sprites)
        sprite = sprites[self.current_frame]
        if not self.facing_right:
            sprite = sprite.transformed(QTransform().scale(-1, 1))
        return sprite

    def get_next_position(self) -> QPoint:
        """Advance position toward the current movement target."""
        if self._carrying_ball:
            self._carry_timer -= 1
            if self._carry_timer <= 0:
                self._carrying_ball = False
                self._walk_target = None
                self.change_state("idle")
            return self.position

        if self.is_chasing and self.target_pos is not None:
            if self._move_toward(self.target_pos.x(), self.target_pos.y(), 5):
                self.stop_chase()
            return self.position

        if self._walk_target is not None:
            speed = 2 if self.state == "walk" else 5
            self._walk_timer -= 1
            if self._walk_timer <= 0:
                self._walk_target = None
                self.change_state("idle")
                return self.position
            if self._move_toward(self._walk_target.x(), self._walk_target.y(), speed):
                self._walk_target = None
                self.change_state("idle")

        return self.position

    def feed(self) -> None:
        """No-op: SimplePet does not eat."""

    def play(self) -> None:
        """No-op: SimplePet plays via ball-chasing instead."""

    def sleep(self) -> None:
        """Enter the lie-down state (user-requested sleep)."""
        self._user_sleep = True
        self._in_idle_behavior = False
        self._walk_target = None
        self.change_state("lie")

    def wake(self) -> None:
        """Exit the lie-down state and return to idle."""
        self._user_sleep = False
        self._in_idle_behavior = False
        self.change_state("idle")

    def pet_action(self) -> None:
        """No-op: SimplePet ignores left-click pets."""

    def save_state(self) -> None:
        """No-op: SimplePet state is not persisted."""

    def load_state(self) -> None:
        """No-op: SimplePet state is not persisted."""

    # -- ball chasing ---------------------------------------------------------

    def chase(self, target_x: float, target_y: float) -> None:
        """Begin chasing the ball at the given screen coordinates."""
        self._walk_target = None
        self.target_pos = QPoint(int(target_x), int(target_y))
        if not self.is_chasing:
            self.is_chasing = True
            self.change_state("run")

    def stop_chase(self) -> None:
        """Stop chasing and begin the carry-ball behaviour."""
        self.is_chasing = False
        self.target_pos = None
        self._start_carry_ball()

    # -- mouse following ------------------------------------------------------

    def tick_mouse_check(self) -> None:
        """Periodic tick that handles spontaneous mouse-following behaviour."""
        if self._user_sleep or self._carrying_ball or self.is_chasing:
            return
        self._spontaneous_counter -= 1
        if self._spontaneous_counter <= 0 and not self._follow_mouse:
            self._spontaneous_counter = random.randint(4500, 18000)
            cursor = QCursor.pos()
            dx = cursor.x() - self.position.x()
            dy = cursor.y() - self.position.y()
            if math.hypot(dx, dy) > 50:
                self._walk_target = QPoint(cursor.x(), cursor.y())
                self._walk_timer = random.randint(20, 60)
                self.change_state("run")
                return

        if self._follow_mouse:
            self._follow_mouse_tick()
            return

        if self._carrying_ball or self.is_chasing or self._walk_target is not None:
            return

        self._mouse_check_counter += 1
        if self._mouse_check_counter < 10:
            return
        self._mouse_check_counter = 0
        cursor = QCursor.pos()
        dx = cursor.x() - self.position.x()
        dy = cursor.y() - self.position.y()
        if math.hypot(dx, dy) < 150 and random.random() < 0.4:
            self._walk_target = QPoint(cursor.x(), cursor.y())
            self._walk_timer = random.randint(30, 80)
            self.change_state("walk")

    # -- state management -----------------------------------------------------

    def change_state(self, new_state: str) -> None:
        """Transition to a new state string, resetting animation counters."""
        if self.state == new_state:
            return
        self.state = new_state
        self.current_frame = 0
        self.frame_counter = 0
        self.is_moving = new_state in ("run", "walk", "with_ball")
        if new_state == "lie" and not self._user_sleep:
            self._lie_timer = 0
            self._auto_sleep_duration = random.randint(8, 16)  # 24–48 s at 3 s/tick

    # -- private helpers ------------------------------------------------------

    def _avail_rect(self):
        return QApplication.desktop().availableGeometry()

    def _calc_anim_speed(self, num_frames: int) -> int:
        return max(1, self._anim_cycle // num_frames)

    def _start_carry_ball(self) -> None:
        self._carrying_ball = True
        self._carry_timer = 60
        self.change_state("with_ball")

    def _start_random_walk(self) -> None:
        rect = self._avail_rect()
        margin = 60
        tx = random.randint(rect.left() + margin, rect.right() - margin)
        ty = random.randint(rect.top() + margin, rect.bottom() - margin)
        self._walk_target = QPoint(tx, ty)
        self._walk_timer = random.randint(60, 200)
        self.change_state("walk")

    def _move_toward(self, tx: int, ty: int, speed: float) -> bool:
        """Move one step toward (tx, ty). Returns True when arrived."""
        dx = tx - self.position.x()
        dy = ty - self.position.y()
        dist = math.hypot(dx, dy)
        if dist < 10:
            return True
        self.facing_right = dx > 0
        rect = self._avail_rect()
        new_x = max(rect.left(), min(int(self.position.x() + dx / dist * speed), rect.right() - 10))
        new_y = max(rect.top(), min(int(self.position.y() + dy / dist * speed), rect.bottom() - 10))
        self.position = QPoint(new_x, new_y)
        return False

    def _follow_mouse_tick(self) -> None:
        cursor = QCursor.pos()
        mouse_moved = cursor != self._mouse_last_pos
        self._mouse_last_pos = cursor

        if mouse_moved and not self._user_sleep:
            self._mouse_still_counter = 0
            self._follow_idle_still_threshold = random.randint(25, 75)
            self._in_idle_behavior = False
            self._walk_target = None
            dx = cursor.x() - self.position.x()
            dy = cursor.y() - self.position.y()
            dist = math.hypot(dx, dy)
            if dist > 15:
                self._walk_target = QPoint(cursor.x(), cursor.y())
                self._walk_timer = 15
                self.change_state("run" if dist >= 200 else "walk")
            else:
                self.change_state("idle")
            return

        if self._in_idle_behavior or self._user_sleep:
            return

        self._mouse_still_counter += 1
        if self._mouse_still_counter >= self._follow_idle_still_threshold:
            self._mouse_still_counter = 0
            self._follow_idle_still_threshold = random.randint(25, 75)
            self._in_idle_behavior = True
            self._walk_target = None
            if random.random() < 0.5:
                self._start_random_walk()
            else:
                self.change_state("lie")
            return

        dx = cursor.x() - self.position.x()
        dy = cursor.y() - self.position.y()
        dist = math.hypot(dx, dy)
        if dist < 15:
            self.change_state("idle")
            return
        self._walk_target = QPoint(cursor.x(), cursor.y())
        self._walk_timer = 15
        self.change_state("run" if dist >= 200 else "walk")
