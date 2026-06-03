# -*- coding: utf-8 -*-
"""Abstract base class that all pet implementations must extend."""
from __future__ import annotations

from abc import ABC, abstractmethod

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPixmap


class BasePet(ABC):
    """Contract ensuring LSP compliance across all concrete pet types.

    Every subclass must set these instance attributes in ``__init__``:
    ``pet_type``, ``name``, ``level``, ``position``, ``is_moving``,
    ``animation_speed``, ``facing_right``.
    """

    # -- abstract interface ------------------------------------------------

    @abstractmethod
    def get_current_sprite(self) -> QPixmap | None:
        """Return the current animation frame, or None if unavailable."""

    @abstractmethod
    def get_next_position(self) -> QPoint:
        """Calculate and return the next on-screen position."""

    @abstractmethod
    def update_stats(self) -> None:
        """Tick internal stats (called once per second)."""

    @abstractmethod
    def decide_next_action(self) -> None:
        """Let the AI pick the pet's next behaviour (called every 3 s)."""

    @abstractmethod
    def check_critical_states(self) -> None:
        """React to critical stat thresholds."""

    @abstractmethod
    def feed(self) -> None:
        """Handle a feed interaction."""

    @abstractmethod
    def play(self) -> None:
        """Handle a play interaction."""

    @abstractmethod
    def sleep(self) -> None:
        """Put the pet to sleep."""

    @abstractmethod
    def wake(self) -> None:
        """Wake the pet up."""

    @abstractmethod
    def pet_action(self) -> None:
        """Handle a left-click interaction."""

    @abstractmethod
    def save_state(self) -> None:
        """Persist current state to storage."""

    @abstractmethod
    def load_state(self) -> None:
        """Restore state from storage."""
