"""Elapsed-time ball physics, with bounded steps for stable collisions."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QRect


class Ball:
    def __init__(self) -> None:
        self.x = self.y = self.vx = self.vy = 0.0
        self.radius = 8
        self.active = False
        self.gravity = 0.5
        self.damping = 0.85
        self.traction = 0.9

    def throw(self, start_x: float, start_y: float, end_x: float, end_y: float) -> None:
        self.x, self.y = float(start_x), float(start_y)
        self.vx = (end_x - start_x) * 0.2
        self.vy = (end_y - start_y) * 0.2
        self.active = True

    def launch(self, x: float, y: float, vx: float, vy: float) -> None:
        """Launch from the released ball center with recent pointer momentum."""
        if not all(math.isfinite(value) for value in (x, y, vx, vy)):
            raise ValueError('Ball launch values must be finite')
        self.x, self.y, self.vx, self.vy = map(float, (x, y, vx, vy))
        self.active = True

    def update(self, dt: float = 0.016, bounds: QRect | None = None) -> None:
        if not self.active:
            return
        dt = max(0.0, min(dt, 0.1))
        if not dt:
            return
        steps = max(1, math.ceil(dt / 0.008))
        tick = dt / steps / 0.016
        if bounds is None:
            from PyQt6.QtCore import QPoint

            from utils.geometry import available_rect
        for _ in range(steps):
            rect = bounds if bounds is not None else available_rect(QPoint(round(self.x), round(self.y)))
            left, right = rect.left() + self.radius, rect.right() - self.radius
            top, bottom = rect.top() + self.radius, rect.bottom() - self.radius
            self.x += self.vx * tick
            self.y += self.vy * tick + 0.5 * self.gravity * tick * tick
            self.vy += self.gravity * tick
            if self.x < left or self.x > right:
                self.x = max(left, min(self.x, right))
                self.vx = -self.vx * self.damping
            if self.y < top:
                self.y = top
                self.vy = abs(self.vy) * self.damping
            if self.y >= bottom:
                self.y = bottom
                self.vy = -abs(self.vy) * self.damping
                self.vx *= self.traction ** tick
                if abs(self.vy) < 0.5:
                    self.vy = 0
            if abs(self.vx) < 0.1 and abs(self.vy) < 0.5 and self.y >= bottom - 1:
                self.y = float(bottom)
                self.vx = self.vy = 0.0
                self.active = False
                break
