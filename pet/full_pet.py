# -*- coding: utf-8 -*-
"""Full-featured pet with stats, autonomous AI, and persistence."""
from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint, QTimer
from PyQt5.QtGui import QPixmap, QTransform

from pet.base_pet import BasePet
from pet.protocols import PetStorage
from pet.state import PetState
from utils.sprite_loader import SpriteLoader

_log = logging.getLogger(__name__)

_FULL_PET_ANIMATIONS = ["idle", "walk", "sleep", "eat", "play", "sit"]


class FullPet(BasePet):
    """Pet with hunger/happiness/energy/health stats and autonomous AI.

    Args:
        pet_type: Sprite-set identifier (e.g. ``"fox"``).
        name: Display name shown in tooltips and dialogs.
        db: Pre-constructed :class:`~utils.database.PetDatabase`; a new
            instance is created automatically when omitted.
    """

    def __init__(
        self,
        pet_type: str = "fox",
        name: str = "Питомец",
        db: PetStorage | None = None,
    ) -> None:
        self.pet_type = pet_type
        self.name = name

        self.hunger: float = 100.0
        self.happiness: float = 100.0
        self.energy: float = 100.0
        self.health: float = 100.0

        self.state = PetState.IDLE
        self.level: int = 1
        self.exp: int = 0

        self.position = QPoint(100, 100)
        self.velocity = QPoint(0, 0)
        self.is_moving = False
        self.facing_right = True

        self.sprite_loader = SpriteLoader(pet_type, _FULL_PET_ANIMATIONS)
        self.current_frame = 0
        self.animation_speed = 5
        self.frame_counter = 0
        self.walk_distance = 0

        # Deferred import avoids circular dependencies at module load time.
        if db is None:
            from utils.database import PetDatabase as _DB
            db = _DB()
        self.db: PetStorage = db
        self.load_state()

    # -- stats ----------------------------------------------------------------

    def update_stats(self) -> None:
        """Decay stats over time and trigger critical-state checks."""
        self.hunger = max(0.0, self.hunger - 0.1)

        if self.state == PetState.SLEEPING:
            self.energy = min(100.0, self.energy + 0.5)
            if self.energy >= 100.0:
                self.change_state(PetState.IDLE)
        else:
            self.energy = max(0.0, self.energy - 0.05)

        if self.hunger < 30 or self.energy < 20:
            self.happiness = max(0.0, self.happiness - 0.2)

        avg = (self.hunger + self.happiness + self.energy) / 3.0
        if avg < 40:
            self.health = max(0.0, self.health - 0.1)
        elif avg > 70:
            self.health = min(100.0, self.health + 0.05)

        self.check_critical_states()

    def check_critical_states(self) -> None:
        """Force idle/sleep when stats reach critical thresholds."""
        if self.state in (
            PetState.EATING, PetState.PLAYING,
            PetState.SLEEPING, PetState.WALKING,
        ):
            return
        if self.hunger < 20:
            self.change_state(PetState.IDLE)
        if self.energy < 15:
            self.sleep()

    # -- AI -------------------------------------------------------------------

    def decide_next_action(self) -> None:
        """Weighted-random AI that selects the next behavioural state."""
        if self.state in (PetState.SLEEPING, PetState.EATING, PetState.WALKING):
            return

        actions: list[str] = []
        if self.hunger < 50:
            actions.extend(["idle"] * 3)
        if self.energy > 70:
            actions.extend(["walk"] * 3)
            actions.extend(["play"] * 2)
        if self.energy < 30:
            actions.extend(["sleep"] * 4)
        actions.extend(["idle", "walk", "sit"])

        choice = random.choice(actions)
        _dispatch = {
            "walk": self.start_walking,
            "sleep": lambda: self.change_state(PetState.SLEEPING),
            "sit": lambda: self.change_state(PetState.SITTING),
            "play": lambda: self.change_state(PetState.PLAYING),
        }
        _dispatch.get(choice, lambda: self.change_state(PetState.IDLE))()

    # -- movement -------------------------------------------------------------

    def start_walking(self) -> None:
        """Begin movement in a random horizontal direction."""
        self.change_state(PetState.WALKING)
        direction = random.choice((-1, 1))
        self.velocity = QPoint(direction * 2, 0)
        self.facing_right = direction > 0
        self.walk_distance = random.randint(50, 200)

    def get_next_position(self) -> QPoint:
        """Advance position by one frame, bouncing off screen edges."""
        if not self.is_moving:
            return self.position

        new_pos = self.position + self.velocity
        screen_width = self._screen_width()

        if new_pos.x() < 0:
            new_pos.setX(0)
            self.velocity.setX(-self.velocity.x())
            self.facing_right = not self.facing_right
        elif new_pos.x() > screen_width - 128:
            new_pos.setX(screen_width - 128)
            self.velocity.setX(-self.velocity.x())
            self.facing_right = not self.facing_right

        self.position = new_pos
        self.walk_distance -= abs(self.velocity.x())
        if self.walk_distance <= 0:
            self.change_state(PetState.IDLE)

        return self.position

    def change_state(self, new_state: PetState) -> None:
        """Transition to a new state, resetting animation counters."""
        self.state = new_state
        self.current_frame = 0
        self.frame_counter = 0
        self.is_moving = new_state == PetState.WALKING

    # -- animation ------------------------------------------------------------

    def get_current_sprite(self) -> QPixmap | None:
        """Return the current animation frame, mirrored when facing left."""
        sprites = self.sprite_loader.get_animation(self.state.value)
        if not sprites:
            return None

        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0
            self.current_frame = (self.current_frame + 1) % len(sprites)

        sprite = sprites[self.current_frame]
        if not self.facing_right:
            sprite = sprite.transformed(QTransform().scale(-1, 1))
        return sprite

    # -- interactions ---------------------------------------------------------

    def feed(self) -> None:
        """Trigger the eat animation and boost hunger/happiness."""
        self.change_state(PetState.EATING)
        self.hunger = min(100.0, self.hunger + 30.0)
        self.happiness = min(100.0, self.happiness + 10.0)
        self.add_exp(5)
        QTimer.singleShot(3000, lambda: self.change_state(PetState.IDLE))

    def play(self) -> None:
        """Trigger the play animation and boost happiness."""
        self.change_state(PetState.PLAYING)
        self.happiness = min(100.0, self.happiness + 20.0)
        self.energy = max(0.0, self.energy - 10.0)
        self.add_exp(10)
        QTimer.singleShot(5000, lambda: self.change_state(PetState.IDLE))

    def sleep(self) -> None:
        """Enter the sleeping state."""
        self.change_state(PetState.SLEEPING)

    def wake(self) -> None:
        """Exit sleep and return to idle."""
        self.change_state(PetState.IDLE)

    def pet_action(self) -> None:
        """Grant small happiness and exp on left-click."""
        self.happiness = min(100.0, self.happiness + 5.0)
        self.add_exp(2)

    def add_exp(self, amount: int) -> None:
        """Add experience points and check for a level-up."""
        self.exp += amount
        if self.exp >= self.level * 100:
            self._level_up()

    def get_mood(self) -> str:
        """Return a human-readable mood string based on current stats."""
        if self.hunger < 30:
            return "голодный 😋"
        if self.energy < 30:
            return "сонный 😴"
        if self.happiness > 80:
            return "счастливый 😊"
        if self.happiness < 40:
            return "грустный 😞"
        return "нормальное 😐"

    # -- persistence ----------------------------------------------------------

    def save_state(self) -> None:
        """Write current state to the database."""
        self.db.save_pet({
            "name": self.name,
            "pet_type": self.pet_type,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "health": self.health,
            "level": self.level,
            "exp": self.exp,
            "position_x": self.position.x(),
            "position_y": self.position.y(),
            "last_save": datetime.now().isoformat(),
        })

    def load_state(self) -> None:
        """Restore state from the database (no-op if no record exists)."""
        data = self.db.load_pet()
        if not data:
            return

        self.name = data.get("name", self.name)
        self.pet_type = data.get("pet_type", self.pet_type)
        self.hunger = float(data.get("hunger", 100.0))
        self.happiness = float(data.get("happiness", 100.0))
        self.energy = float(data.get("energy", 100.0))
        self.health = float(data.get("health", 100.0))
        self.level = int(data.get("level", 1))
        self.exp = int(data.get("exp", 0))
        self.position = QPoint(
            int(data.get("position_x", 100)),
            int(data.get("position_y", 100)),
        )
        last_save = data.get("last_save")
        if last_save:
            self._apply_time_decay(last_save)

    # -- private helpers ------------------------------------------------------

    def _level_up(self) -> None:
        self.level += 1
        self.exp = 0
        self.hunger = self.happiness = self.energy = self.health = 100.0
        _log.info("%s достиг уровня %d!", self.name, self.level)

    def _apply_time_decay(self, last_save_str: str) -> None:
        try:
            elapsed_min = (
                datetime.now() - datetime.fromisoformat(last_save_str)
            ).total_seconds() / 60.0
            elapsed_min = min(elapsed_min, 1440.0)
            self.hunger = max(0.0, self.hunger - elapsed_min * 0.5)
            self.energy = max(0.0, self.energy - elapsed_min * 0.3)
            if self.hunger < 50:
                self.happiness = max(0.0, self.happiness - elapsed_min * 0.2)
        except ValueError:
            _log.warning("Could not parse last_save timestamp: %s", last_save_str)

    def _screen_width(self) -> int:
        from PyQt5.QtWidgets import QApplication
        return QApplication.desktop().screenGeometry().width()
