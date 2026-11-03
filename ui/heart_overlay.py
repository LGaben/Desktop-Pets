"""Noninteractive desktop overlay; lifetime is driven by the pet's existing tick."""
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from ui.heart_effect import DURATION, HEART_MASK, HEIGHT, WIDTH, hearts_at
from utils.geometry import available_rect, clamp_position


class HeartOverlay(QWidget):
    def __init__(self, owner):
        super().__init__(owner, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.WindowTransparentForInput | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(WIDTH, HEIGHT)
        self.started = None
        self.elapsed = 0.0

    @property
    def active(self):
        return self.started is not None

    def start(self, now):
        if self.active:
            return
        self.started = now
        self.tick(now)
        self.show()
        self.raise_()

    def stop(self):
        self.started = None
        self.hide()

    def tick(self, now):
        if not self.active:
            return
        self.elapsed = max(0, now - self.started)
        if self.elapsed >= DURATION:
            self.stop()
            return
        owner = self.parentWidget()
        head_x = owner.width() // 2
        if owner.pet.pet_type == 'fox':
            head_x = 34 if owner.pet.facing_right else owner.width() - 34
        point = owner.pos() + QPoint(head_x - WIDTH // 2, -48)
        self.move(clamp_position(point, self.size(), available_rect(owner.pos())))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y, scale, alpha in hearts_at(self.elapsed):
            painter.setBrush(QColor(255, 100 if scale == 2 else 145, 160 if scale == 2 else 185, alpha))
            for row, pixels in enumerate(HEART_MASK):
                for column, filled in enumerate(pixels):
                    if filled == '1':
                        painter.drawRect(x + column * scale, y + row * scale, scale, scale)
