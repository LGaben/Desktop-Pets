"""A visible, directly grabbable ball with recent-pointer release momentum."""
from time import monotonic

from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from utils.geometry import available_rect, clamp_position
from utils.i18n import t
from utils.throw_gesture import ThrowGesture


class BallWidget(QWidget):
    def __init__(self, ball, pet_window):
        super().__init__(pet_window)
        self.ball = ball
        self.pet_window = pet_window
        self.grabbing = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip(t('ball_grab_hint'))
        self.resize(32, 32)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._last_tick = monotonic()
        self._place()

    def _place(self):
        self.move(round(self.ball.x - self.width() / 2), round(self.ball.y - self.height() / 2))
        self.update()

    def start(self):
        self._last_tick = monotonic()
        self._place()
        self.show()
        if self.ball.active:
            self.timer.start(16)

    def cleanup(self):
        self.cancel_grab(restore=False)
        self.timer.stop()
        self.ball.active = False
        self.hide()
        self.deleteLater()

    def cancel_grab(self, restore=True):
        if not self.grabbing:
            return
        self.grabbing = False
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        if QWidget.keyboardGrabber() is self:
            self.releaseKeyboard()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if restore:
            self.ball.x, self.ball.y = self._grab_origin
            self.ball.active = False
            self._place()

    def hideEvent(self, event):
        self.cancel_grab(restore=False)
        self.timer.stop()
        super().hideEvent(event)

    def event(self, event):
        if (event.type() in (QEvent.Type.UngrabMouse, QEvent.Type.WindowDeactivate)
                and getattr(self, 'grabbing', False)):
            self.cancel_grab()
        return super().event(event)

    def closeEvent(self, event):
        self.cancel_grab(restore=False)
        self.timer.stop()
        self.ball.active = False
        super().closeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(46, 216, 81))
        painter.setPen(Qt.PenStyle.NoPen)
        r = self.ball.radius
        painter.drawEllipse(self.width() // 2 - r, self.height() // 2 - r, r * 2, r * 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.cancel_grab()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.timer.stop()
            self.pet_window.on_ball_grab()
            self._grab_origin = self.ball.x, self.ball.y
            self._pointer_offset = event.globalPosition().toPoint() - QPoint(round(self.ball.x), round(self.ball.y))
            self.ball.active = False
            self.grabbing = True
            self.gesture = ThrowGesture()
            self.gesture.add(self.ball.x, self.ball.y, monotonic())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.grabMouse()
            self.grabKeyboard()

    def _drag_to(self, point):
        center = point - self._pointer_offset
        top_left = center - QPoint(self.width() // 2, self.height() // 2)
        position = clamp_position(top_left, self.size(), available_rect(center))
        self.ball.x = position.x() + self.width() / 2
        self.ball.y = position.y() + self.height() / 2
        self._place()

    def mouseMoveEvent(self, event):
        if self.grabbing:
            self._drag_to(event.globalPosition().toPoint())
            self.gesture.add(self.ball.x, self.ball.y, monotonic())

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.grabbing:
            return
        self._drag_to(event.globalPosition().toPoint())
        vx, vy = self.gesture.release(self.ball.x, self.ball.y, monotonic())
        self.cancel_grab(restore=False)
        self.ball.launch(self.ball.x, self.ball.y, vx, vy)
        self._last_tick = monotonic()
        self.timer.start(16)
        self.pet_window.on_ball_move(self.ball.x, self.ball.y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_grab()
        else:
            super().keyPressEvent(event)

    def _tick(self):
        now = monotonic()
        self.ball.update(now - self._last_tick)
        self._last_tick = now
        self._place()
        self.pet_window.on_ball_move(self.ball.x, self.ball.y)
        if not self.ball.active:
            self.timer.stop()
