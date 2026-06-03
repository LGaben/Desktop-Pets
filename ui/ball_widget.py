# -*- coding: utf-8 -*-
"""Transparent overlay widget that renders the bouncing ball."""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget


class BallWidget(QWidget):
    """Frameless widget that paints the ball and drives its physics loop.

    Args:
        ball: The :class:`~pet.ball.Ball` physics object to render.
        pet_window: Parent :class:`~ui.pet_window.PetWindow` that receives
            position callbacks via :meth:`~ui.pet_window.PetWindow.on_ball_move`.
    """

    def __init__(self, ball, pet_window) -> None:
        super().__init__()
        self.ball = ball
        self.pet_window = pet_window

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        size = ball.radius * 4
        self.resize(size, size)
        self.move(int(ball.x - ball.radius), int(ball.y - ball.radius))

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def paintEvent(self, event) -> None:
        if not self.ball.active:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(46, 216, 81))
        painter.setPen(Qt.NoPen)
        r = self.ball.radius
        w = self.width()
        painter.drawEllipse(int(w / 2 - r), int(w / 2 - r), int(r * 2), int(r * 2))

    def _tick(self) -> None:
        self.ball.update()
        if not self.ball.active:
            self.hide()
            self.timer.stop()
            return
        avail = QApplication.desktop().availableGeometry()
        bx = max(avail.x() + self.ball.radius, min(self.ball.x, avail.right() - self.ball.radius))
        by = max(avail.y() + self.ball.radius, min(self.ball.y, avail.bottom() - self.ball.radius))
        self.move(int(bx - self.ball.radius), int(by - self.ball.radius))
        self.pet_window.on_ball_move(bx, by)
        self.update()
