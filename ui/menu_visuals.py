"""Shared native menu palette and small, locally painted action icons."""
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen, QPixmap
from PyQt6.QtWidgets import QApplication

from utils.i18n import t


def colors():
    dark = QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128
    return dict(surface='#242321' if dark else '#fbfaf7', text='#f3f0ea' if dark else '#292723',
                muted='#b9b3a9' if dark else '#726c63', line='#48443e' if dark else '#e6e0d6',
                hover='#38312a' if dark else '#f3e7d8', pressed='#493626' if dark else '#ecd6bd',
                accent='#edaa71' if dark else '#a94e19')


def menu_stylesheet():
    c = colors()
    return f"""
    QFrame#interactionPanel {{ background:transparent; border:0; }}
    QWidget#petActions, QScrollArea, QScrollArea > QWidget > QWidget {{ background:transparent; border:0; }}
    QWidget#petProfile {{ background:{c['surface']}; border:1px solid {c['line']}; border-radius:16px; }}
    QPushButton#petProfile {{ padding:0; }}
    QPushButton#petProfile:hover, QPushButton#petProfile:focus {{ background:{c['hover']}; border-color:{c['accent']}; }}
    QPushButton#petProfile:pressed {{ background:{c['pressed']}; }}
    QLabel {{ color:{c['text']}; background:transparent; border:0; }}
    QLabel#petCharacter {{ color:{c['muted']}; }}
    QLabel#petName {{ font-weight:600; }}
    QPushButton {{ color:{c['text']}; background:transparent; border:1px solid transparent;
        border-radius:8px; padding:0 12px; text-align:left; }}
    QPushButton:hover {{ background:{c['hover']}; }}
    QPushButton:pressed {{ background:{c['pressed']}; }}
    QPushButton:focus {{ border-color:{c['accent']}; background:{c['hover']}; }}
    QPushButton#menuStyleOption {{ text-align:center; padding:0 6px; border-color:{c['line']}; }}
    QPushButton#menuStyleOption:checked {{ color:{c['accent']}; background:{c['hover']}; border-color:{c['accent']}; }}
    QPushButton#ringAction {{ background:{c['surface']}; border-color:{c['line']}; border-radius:16px; padding:0 8px; }}
    QPushButton#ringAction:hover, QPushButton#ringAction:focus {{ background:{c['hover']}; border-color:{c['accent']}; }}
    QPushButton#ringAction:pressed {{ background:{c['pressed']}; }}
    QPushButton#settingsShortcut {{ padding:0; text-align:center; }}
    QPushButton::menu-indicator {{ width:0; height:0; }}
    QFrame#actionDivider {{ background:{c['line']}; border:0; max-height:1px; }}
    QMenu {{ color:{c['text']}; background:{c['surface']}; border:1px solid {c['line']}; padding:6px; font:10pt 'Segoe UI'; }}
    QMenu::item {{ padding:10px 22px 10px 12px; border-radius:6px; }}
    QMenu::item:selected {{ background:{c['hover']}; color:{c['text']}; }}
    QMenu::item:disabled {{ color:{c['muted']}; }}
    QMenu::separator {{ height:1px; background:{c['line']}; margin:5px 8px; }}
    """


def action_icon(label):
    keys = ('pet_action', 'ball_action', 'sleep', 'wake_up', 'settings', 'more_actions',
            'start_follow', 'stop_follow', 'app_actions', 'add_pet', 'quit', 'remove_pet', 'hide_to_tray')
    key = next((key for key in keys if t(key) == label), 'more_actions')
    image = QPixmap(24, 24)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(colors()['accent'] if key == 'pet_action' else colors()['text']),
                        1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if key == 'pet_action':
        path = QPainterPath(QPointF(12, 20))
        path.cubicTo(9, 17, 2, 12, 4, 7)
        path.cubicTo(6, 3, 11, 4, 12, 7)
        path.cubicTo(15, 2, 21, 4, 21, 9)
        path.cubicTo(21, 13, 15, 18, 12, 20)
        painter.drawPath(path)
    elif key == 'ball_action':
        painter.drawEllipse(QRectF(4, 4, 16, 16))
        painter.drawArc(QRectF(1, 4, 15, 16), -65 * 16, 130 * 16)
        painter.drawLine(7, 5, 18, 18)
    elif key in ('sleep', 'wake_up'):
        path = QPainterPath(QPointF(17, 4))
        path.cubicTo(2, 0, 0, 21, 15, 21)
        path.cubicTo(19, 21, 21, 18, 21, 15)
        path.cubicTo(12, 18, 9, 9, 17, 4)
        painter.drawPath(path)
    elif key in ('settings', 'app_actions'):
        painter.drawEllipse(QRectF(6, 6, 12, 12))
        painter.drawEllipse(QRectF(10, 10, 4, 4))
        for x1, y1, x2, y2 in ((12, 2, 12, 5), (12, 19, 12, 22), (2, 12, 5, 12), (19, 12, 22, 12),
                                 (5, 5, 7, 7), (17, 17, 19, 19), (5, 19, 7, 17), (17, 7, 19, 5)):
            painter.drawLine(x1, y1, x2, y2)
    elif key in ('start_follow', 'stop_follow'):
        painter.drawLine(5, 3, 5, 20)
        painter.drawLine(5, 3, 19, 14)
        painter.drawLine(5, 20, 10, 14)
        painter.drawLine(10, 14, 19, 14)
    elif key == 'hide_to_tray':
        painter.drawLine(5, 19, 19, 19)
        painter.drawLine(12, 3, 12, 15)
        painter.drawLine(7, 10, 12, 15)
        painter.drawLine(12, 15, 17, 10)
    elif key == 'quit':
        painter.drawArc(QRectF(4, 4, 16, 16), 130 * 16, 280 * 16)
        painter.drawLine(12, 2, 12, 12)
    elif key in ('add_pet', 'remove_pet'):
        painter.drawLine(5, 12, 19, 12)
        if key == 'add_pet':
            painter.drawLine(12, 5, 12, 19)
    else:
        for x in (5, 12, 19):
            painter.drawEllipse(QRectF(x - 1, 11, 2, 2))
    painter.end()
    return QIcon(image)
