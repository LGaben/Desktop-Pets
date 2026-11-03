# -*- coding: utf-8 -*-
"""Runtime-checkable protocols defining pet capability contracts."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class HasStats(Protocol):
    """Protocol for pets that maintain quantified vitality statistics."""

    hunger: float
    happiness: float
    energy: float
    health: float
    exp: int

    def get_mood(self) -> str: ...
    def feed(self) -> None: ...
    def play(self) -> None: ...
    def add_exp(self, amount: int) -> None: ...


@runtime_checkable
class BallChaser(Protocol):
    """Protocol for pets that can chase a thrown ball."""

    carrying_ball: bool

    def chase(self, target_x: float, target_y: float) -> None: ...
    def stop_chase(self) -> None: ...
    def cancel_chase(self) -> None: ...


@runtime_checkable
class MouseFollower(Protocol):
    """Protocol for pets that can autonomously track the mouse cursor."""

    following_mouse: bool

    def set_follow_mouse(self, enabled: bool) -> None: ...

    def tick_mouse_check(self) -> None: ...


@runtime_checkable
class PetStorage(Protocol):
    """Protocol for pet-state persistence backends (DIP: FullPet depends on
    this abstraction, not on the concrete PetDatabase class)."""

    def save_pet(self, data: dict) -> None: ...
    def load_pet(self) -> dict | None: ...
