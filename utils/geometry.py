"""Screen selection and bounds calculations shared by pets and ball physics."""
from PyQt6.QtCore import QPoint, QRect, QSize
from PyQt6.QtWidgets import QApplication


def nearest_rect(point: QPoint, rects: list[QRect]) -> QRect:
    """Choose the containing screen, or the closest screen after hot unplug."""
    if not rects:
        return QRect(0, 0, 800, 600)
    def distance(rect):
        dx = max(rect.left() - point.x(), 0, point.x() - rect.right())
        dy = max(rect.top() - point.y(), 0, point.y() - rect.bottom())
        return dx * dx + dy * dy
    return min(rects, key=distance)


def available_rect(point: QPoint) -> QRect:
    return nearest_rect(point, [s.availableGeometry() for s in QApplication.screens()])


def clamp_position(point: QPoint, size: QSize, rect: QRect) -> QPoint:
    """Clamp a window's top left, accounting for inclusive QRect edges."""
    return QPoint(
        max(rect.left(), min(point.x(), max(rect.left(), rect.right() - size.width() + 1))),
        max(rect.top(), min(point.y(), max(rect.top(), rect.bottom() - size.height() + 1))),
    )


def movement_bounds(point: QPoint, size: QSize) -> QRect:
    rect = available_rect(point)
    corner = clamp_position(rect.bottomRight(), size, rect)
    return QRect(rect.topLeft(), corner)
