# -*- coding: utf-8 -*-
"""Simplified pet (no stats) that chases balls and follows the mouse."""
from __future__ import annotations

import math
import random
from time import monotonic

from PyQt6.QtCore import QPoint, QPointF
from PyQt6.QtGui import QCursor, QPixmap

from pet.base_pet import BasePet
from pet.cursor_reaction import CursorReaction
from pet.fox_personality import FOX_PERSONALITIES, choose_personality, idle_action
from pet.fox_reaction import FoxReaction
from utils.geometry import available_rect, clamp_position, movement_bounds
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

    def __init__(self, pet_type: str = "fox", name: str | None = None,
                 personality_id: str | None = None) -> None:
        self.pet_type = pet_type
        self.personality_id = choose_personality(personality_id) if pet_type == 'fox' else None
        self._pet_reaction = FoxReaction()
        self.name = name or t(f"name_{pet_type}")
        self.level: int = 1

        self.state = "idle"
        self.is_moving = False
        self.facing_right = True
        self.position = QPoint(100, 100)
        self.velocity = QPoint(0, 0)
        self._precise_position = QPointF(self.position)

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
        self._follow_mouse = False
        self._cursor_reaction = CursorReaction()
        self._cursor_moving = False
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
        if self._pet_reaction.active:
            return
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
        if self.personality_id:
            action = idle_action(self.personality_id, r)
        else:
            action = 'walk' if r < .45 else 'lie' if r < .55 else 'idle'
        if action == 'walk':
            self._start_random_walk()
        elif action == 'lie':
            self.change_state("lie")

    def get_current_sprite(self, dt: float = 0.033) -> QPixmap | None:
        """Return the current animation frame, mirrored when facing left."""
        sprites = self.sprite_loader.get_animation(self.state, mirrored=not self.facing_right)
        if not sprites:
            return None
        speed = self._calc_anim_speed(len(sprites))
        self.frame_counter += max(0.0, min(dt, 0.1)) / 0.033
        frames, self.frame_counter = divmod(self.frame_counter, speed)
        self.current_frame = (self.current_frame + int(frames)) % len(sprites)
        if self.pet_type == 'fox' and self.state == 'idle':
            self._pet_reaction.advance(max(0.0, min(dt, .1)))
            if head := self._pet_reaction.head:
                poses = self.sprite_loader.get_animation(f'pet_react/head_{head}', mirrored=not self.facing_right)
                return poses[self.current_frame % len(poses)]
        return sprites[self.current_frame]

    def get_next_position(self, dt: float = 0.033) -> QPoint:
        """Advance position toward the current movement target."""
        ticks = max(0.0, min(dt, 0.1)) / 0.033
        if self._carrying_ball:
            self._carry_timer -= ticks
            if self._carry_timer <= 0:
                self._carrying_ball = False
                self._walk_target = None
                self.change_state("idle")
            return self.position

        if self.is_chasing and self.target_pos is not None:
            if self._move_toward(self.target_pos.x(), self.target_pos.y(), 5 * ticks):
                self.stop_chase()
            return self.position

        if self._walk_target is not None:
            speed = 2 if self.state == "walk" else 5
            self._walk_timer -= ticks
            if self._walk_timer <= 0:
                self._walk_target = None
                self.change_state("idle")
                return self.position
            if self._move_toward(self._walk_target.x(), self._walk_target.y(), speed * ticks):
                self._walk_target = None
                self.change_state("idle")

        return self.position

    def feed(self) -> None:
        """No-op: SimplePet does not eat."""

    def play(self) -> None:
        """No-op: SimplePet plays via ball-chasing instead."""

    def sleep(self) -> None:
        """Enter the lie-down state (user-requested sleep)."""
        self.cancel_chase()
        self._user_sleep = True
        self._walk_target = None
        self.change_state("lie")

    def wake(self) -> None:
        """Exit the lie-down state and return to idle."""
        self._user_sleep = False
        self.change_state("idle")

    def pet_action(self) -> bool:
        """Accept hearts; only a fox also reacts with its head."""
        if self._user_sleep or self._pet_reaction.active:
            return False
        if self.pet_type != 'fox':
            return True
        self.cancel_chase()
        self._walk_target = None
        self.change_state('idle')
        self._pet_reaction.start()
        return True

    def pause(self) -> None:
        self._pet_reaction.cancel()
        self.reset_cursor_reaction()

    def resume(self) -> None:
        self.reset_cursor_reaction()

    def cancel_interaction(self) -> None:
        self._pet_reaction.cancel()
        self.reset_cursor_reaction()

    @property
    def petting(self) -> bool:
        return self._pet_reaction.active

    def save_state(self) -> None:
        """Ask the owning application to persist this pet in its roster."""
        if callback := getattr(self, "_state_saver", None):
            callback()

    def load_state(self) -> None:
        """Roster restoration is handled by the owning application."""

    # -- ball chasing ---------------------------------------------------------

    def chase(self, target_x: float, target_y: float) -> None:
        """Begin chasing the ball at the given screen coordinates."""
        if self._user_sleep:
            return
        self.reset_cursor_reaction()
        self._walk_target = None
        target = QPoint(round(target_x - self.window_size.width() / 2),
                        round(target_y - self.window_size.height() / 2))
        self.target_pos = clamp_position(target, self.window_size, available_rect(target))
        if not self.is_chasing:
            self.is_chasing = True
            self.change_state("run")

    @property
    def carrying_ball(self) -> bool:
        return self._carrying_ball

    @property
    def following_mouse(self) -> bool:
        return self._follow_mouse

    def set_follow_mouse(self, enabled: bool) -> None:
        self.reset_cursor_reaction()
        self._follow_mouse = bool(enabled)
        self._walk_target = None
        if not self._user_sleep and not self.is_chasing and not self._carrying_ball:
            self.change_state("idle")

    def cancel_chase(self) -> None:
        self.reset_cursor_reaction()
        self.is_chasing = False
        self.target_pos = None
        self._carrying_ball = False
        self._carry_timer = 0
        self._walk_target = None
        if not self._user_sleep:
            self.change_state("idle")

    def stop_chase(self) -> None:
        """Stop chasing and begin the carry-ball behaviour."""
        self.is_chasing = False
        self.target_pos = None
        self._start_carry_ball()

    # -- mouse following ------------------------------------------------------

    def tick_mouse_check(self) -> None:
        """React to actual nearby cursor motion without interrupting explicit actions."""
        if self.state == 'lie' or self._carrying_ball or self.is_chasing or self._pet_reaction.active:
            self.reset_cursor_reaction()
            return
        if self._follow_mouse:
            self._follow_mouse_tick()
            return
        cursor = QCursor.pos()
        rect = self._avail_rect()
        plan = self._cursor_reaction.sample(
            (cursor.x(), cursor.y()), (self.position.x(), self.position.y()),
            (self.window_size.width(), self.window_size.height()),
            (rect.left(), rect.top(), rect.right(), rect.bottom()),
            monotonic(), self.personality_id)
        if plan:
            x, y, animation = plan
            if animation == 'idle':
                if self._cursor_moving:
                    self._walk_target = None
                    self.change_state('idle')
                return
            self._walk_target = QPoint(x, y)
            self._walk_timer = 24
            self._cursor_moving = True
            self.change_state(animation)

    def reset_cursor_reaction(self, sampled_at=None) -> None:
        cursor = QCursor.pos()
        self._cursor_reaction.reset((cursor.x(), cursor.y()))
        self._cursor_reaction.last_sample = sampled_at
        if self._cursor_moving:
            self._walk_target = None
            self._cursor_moving = False
            if not (self._user_sleep or self.is_chasing or self._carrying_ball):
                self.change_state('idle')

    def hold_for_interaction(self) -> None:
        """Stop free walking for a click; keep explicit follow and ball ownership."""
        self.reset_cursor_reaction()
        if not (self._follow_mouse or self.is_chasing or self._carrying_ball) and self.state in ('walk', 'run'):
            self._walk_target = None
            self.change_state('idle')

    # -- state management -----------------------------------------------------

    def change_state(self, new_state: str) -> None:
        """Transition to a new state string, resetting animation counters."""
        if self.state == new_state:
            return
        self._pet_reaction.cancel()
        self.state = new_state
        if new_state not in ('walk', 'run'):
            self._cursor_moving = False
        self.current_frame = 0
        self.frame_counter = 0
        self.is_moving = new_state in ("run", "walk", "with_ball")
        if new_state == "lie" and not self._user_sleep:
            self._lie_timer = 0
            limits = FOX_PERSONALITIES[self.personality_id].rest_ticks if self.personality_id else (8, 16)
            self._auto_sleep_duration = random.randint(*limits)

    # -- private helpers ------------------------------------------------------

    def _avail_rect(self):
        return movement_bounds(self.position, self.window_size)

    def _calc_anim_speed(self, num_frames: int) -> int:
        return max(1, self._anim_cycle // num_frames)

    def _start_carry_ball(self) -> None:
        self._carrying_ball = True
        self._carry_timer = 30 + 90 * FOX_PERSONALITIES[self.personality_id].ball_interest if self.personality_id else 60
        self.change_state("with_ball")

    def _start_random_walk(self) -> None:
        self._cursor_moving = False
        rect = self._avail_rect()
        tx = random.randint(rect.left(), rect.right())
        ty = random.randint(rect.top(), rect.bottom())
        self._walk_target = QPoint(tx, ty)
        self._walk_timer = random.randint(60, 200)
        self.change_state("walk")

    def _move_toward(self, tx: int, ty: int, speed: float) -> bool:
        """Move one step toward (tx, ty). Returns True when arrived."""
        if self._precise_position.toPoint() != self.position:
            self._precise_position = QPointF(self.position)
        dx = tx - self._precise_position.x()
        dy = ty - self._precise_position.y()
        dist = math.hypot(dx, dy)
        if dist <= max(10, speed):
            return True
        self.facing_right = dx > 0
        rect = self._avail_rect()
        new_x = max(rect.left(), min(self._precise_position.x() + dx / dist * speed, rect.right()))
        new_y = max(rect.top(), min(self._precise_position.y() + dy / dist * speed, rect.bottom()))
        self._precise_position = QPointF(new_x, new_y)
        self.position = self._precise_position.toPoint()
        return False

    def _follow_mouse_tick(self) -> None:
        """Explicit Follow stays enabled until the user turns it off."""
        cursor = QCursor.pos()
        dx = cursor.x() - (self.position.x() + self.window_size.width() / 2)
        dy = cursor.y() - (self.position.y() + self.window_size.height() / 2)
        dist = math.hypot(dx, dy)
        if dist <= 48:
            self._walk_target = None
            self.change_state("idle")
            return
        point = QPoint(round(self.position.x() + dx * (dist - 48) / dist),
                       round(self.position.y() + dy * (dist - 48) / dist))
        self._walk_target = clamp_position(point, self.window_size, available_rect(self.position))
        if math.hypot(self._walk_target.x() - self.position.x(),
                      self._walk_target.y() - self.position.y()) <= 10:
            self._walk_target = None
            self.change_state('idle')
            return
        self._walk_timer = 15
        self.change_state("run" if dist >= 200 else "walk")
