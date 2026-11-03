# -*- coding: utf-8 -*-
"""Abstract base class that all pet implementations must extend."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtGui import QPixmap


class BasePet(ABC):
    """Contract ensuring LSP compliance across all concrete pet types.

    Every subclass must set these instance attributes in ``__init__``:
    ``pet_type``, ``name``, ``level``, ``position``, ``is_moving``,
    ``animation_speed``, ``facing_right``.
    """

    window_size = QSize(64, 64)

    def pause(self) -> None:
        """Suspend model-owned activity when the window is hidden."""

    def resume(self) -> None:
        """Resume model-owned activity."""

    def cleanup(self) -> None:
        self.pause()

    def set_state_saver(self, callback: Callable[[], None] | None) -> None:
        self._state_saver = callback

    # -- abstract interface ------------------------------------------------

    @abstractmethod
    def get_current_sprite(self, dt: float = 0.033) -> QPixmap | None:
        """Return the current animation frame, or None if unavailable."""

    @abstractmethod
    def get_next_position(self, dt: float = 0.033) -> QPoint:
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
    def pet_action(self) -> bool:
        """Handle a left-click interaction; report whether a new action began."""

    @abstractmethod
    def save_state(self) -> None:
        """Persist current state to storage."""

    @abstractmethod
    def load_state(self) -> None:
        """Restore state from storage."""
