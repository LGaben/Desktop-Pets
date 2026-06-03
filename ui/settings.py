from __future__ import annotations

import math

from PyQt5.QtCore import (
    QEasingCurve, QPoint, QPointF, QPropertyAnimation,
    QRect, QRectF, Qt, QTimer, pyqtProperty, pyqtSignal,
)
from PyQt5.QtGui import (
    QColor, QFont, QLinearGradient,
    QPainter, QPainterPath, QPen, QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from utils.i18n import t, get_lang, save_lang, save_pet
from utils.paths import resource_base

# ---------------------------------------------------------------------------
# Cyberpunk palette
# ---------------------------------------------------------------------------
_CYAN      = QColor(0, 230, 255)
_CYAN_DIM  = QColor(0, 180, 210)
_ORANGE    = QColor(255, 150, 0)
_BG_DEEP   = QColor(8, 10, 20)
_INPUT_BG  = QColor(6, 8, 18)
_GRID_LINE = QColor(0, 200, 230, 40)

_ACCENT_CYAN   = "#00e6ff"
_ACCENT_ORANGE = "#ff9600"

_PET_TYPES = [
    "fox", "panda", "cockatiel",
    "dog", "turtle", "totoro",
    "chicken", "clippy", "crab", "deno", "horse",
    "mod", "monkey", "morph", "rat", "rocky",
    "rubber_duck", "skeleton", "snail", "snake", "zappy",
]

_PET_EMOJI: dict[str, str] = {
    "fox":        "🦊",
    "panda":      "🐼",
    "cockatiel":  "🐦",
    "dog":        "🐕",
    "turtle":     "🐢",
    "totoro":     "🐻",
    "chicken":    "🐔",
    "clippy":     "📎",
    "crab":       "🦀",
    "deno":       "🦕",
    "horse":      "🐴",
    "mod":        "🔮",
    "monkey":     "🐒",
    "morph":      "💜",
    "rat":        "🐀",
    "rocky":      "🪨",
    "rubber_duck":"🦆",
    "skeleton":   "💀",
    "snail":      "🐌",
    "snake":      "🐍",
    "zappy":      "⚡",
}

_W, _H   = 420, 560
_TITLE_H = 52
_RADIUS  = 14
_FONT    = "Consolas"

_CSS = f"""
    QWidget  {{ font-family:Consolas,"Segoe UI",Arial,sans-serif; }}
    QLabel   {{ color:{_ACCENT_CYAN}; background:transparent; border:none; }}
    QLineEdit {{
        background:{_INPUT_BG.name()}; color:{_ACCENT_CYAN};
        border:1px solid {_CYAN_DIM.name()}; border-radius:6px;
        padding:8px 14px; font-size:13px; font-weight:bold;
    }}
    QLineEdit:focus {{
        border:1px solid {_ACCENT_CYAN};
        background:rgb(8,12,24);
    }}
    QPushButton {{
        font-weight:bold; border:1px solid; border-radius:8px;
        padding:9px 0; font-size:13px; letter-spacing:1px;
    }}
    QPushButton#apply {{
        background:rgba(255,150,0,25); color:{_ACCENT_ORANGE};
        border-color:{_ACCENT_ORANGE};
    }}
    QPushButton#apply:hover  {{ background:rgba(255,150,0,45); border-color:#ffb040; }}
    QPushButton#apply:pressed {{ background:rgba(255,150,0,60); }}
    QPushButton#cancel {{
        background:rgba(0,230,255,12); color:{_ACCENT_CYAN};
        border-color:{_CYAN_DIM.name()};
    }}
    QPushButton#cancel:hover  {{ background:rgba(0,230,255,30); border-color:{_ACCENT_CYAN}; }}
    QPushButton#cancel:pressed {{ background:rgba(0,230,255,45); }}
    QPushButton#cls {{
        background:transparent; border:none;
        color:rgba(0,230,255,80); font-size:18px;
        padding:2px 8px; border-radius:6px;
    }}
    QPushButton#cls:hover {{ color:{_ACCENT_CYAN}; background:rgba(0,230,255,20); }}
    QPushButton#rm {{
        background:rgba(255,50,50,12); color:rgba(255,90,90,200);
        border:1px solid rgba(255,60,60,80); border-radius:5px;
        font-size:11px; letter-spacing:0px; padding:3px 8px;
    }}
    QPushButton#rm:hover  {{ background:rgba(255,50,50,30); border-color:rgba(255,80,80,180); }}
    QPushButton#rm:pressed {{ background:rgba(255,50,50,50); }}
    QPushButton#add_pet_btn_main {{
        background:rgba(0,230,255,12); color:{_ACCENT_CYAN};
        border-color:{_CYAN_DIM.name()};
    }}
    QPushButton#add_pet_btn_main:hover {{
        background:rgba(0,230,255,30); border-color:{_ACCENT_CYAN};
    }}
    QPushButton#add_pet_btn_main:pressed {{
        background:rgba(0,230,255,45);
    }}
    QScrollArea {{
        background:transparent; border:none;
    }}
    QScrollBar:vertical {{
        background:rgba(0,0,0,0); width:6px; margin:0;
    }}
    QScrollBar::handle:vertical {{
        background:rgba(0,230,255,60); border-radius:3px; min-height:20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background:transparent;
    }}
"""


# ---------------------------------------------------------------------------
# GlowLabel
# ---------------------------------------------------------------------------
class GlowLabel(QLabel):
    def __init__(
        self, text: str, color: QColor = _CYAN,
        size: int = 11, bold: bool = False,
        blur: int = 14, tracking: int = 0,
    ) -> None:
        super().__init__(text)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        f = QFont(_FONT, size)
        f.setBold(bold)
        if tracking:
            f.setLetterSpacing(QFont.PercentageSpacing, 100 + tracking)
        self.setFont(f)
        self.setStyleSheet(f"color:{color.name()}; background:transparent;")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setColor(QColor(color.red(), color.green(), color.blue(), 180))
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)


def _section_label(text: str) -> GlowLabel:
    return GlowLabel(text, _CYAN_DIM, 9, blur=10, tracking=2)


# ---------------------------------------------------------------------------
# HologramCard
# ---------------------------------------------------------------------------
class HologramCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(
        self, pet_type: str, display_name: str,
        pixmap: QPixmap, selected: bool = False,
    ) -> None:
        super().__init__()
        self.pet_type  = pet_type
        self._selected = selected
        self._wire_angle = 0.0

        self.setFixedSize(78, 88)
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.NoFrame)

        col = QVBoxLayout(self)
        col.setContentsMargins(4, 6, 4, 4)
        col.setSpacing(2)
        col.setAlignment(Qt.AlignCenter)

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignCenter)
        self._img_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        if not pixmap.isNull():
            self._img_label.setPixmap(
                pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self._img_label.setText("?")
            self._img_label.setStyleSheet(f"font-size:20px; color:{_ACCENT_CYAN};")
        col.addWidget(self._img_label)

        self._name_lbl = GlowLabel(display_name, _CYAN_DIM, 9, blur=7)
        self._name_lbl.setAlignment(Qt.AlignCenter)
        col.addWidget(self._name_lbl)

        self._hl_anim = QPropertyAnimation(self, b"hl")
        self._hl_anim.setDuration(220)
        self._hl_anim.setEasingCurve(QEasingCurve.OutCubic)

    def set_display_name(self, name: str) -> None:
        self._name_lbl.setText(name)

    # -- paint ---------------------------------------------------------------

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rc = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        bar = QRectF(rc.x() + 8, rc.bottom() - 18, rc.width() - 16, 3)
        grad = QLinearGradient(bar.topLeft(), bar.topRight())
        c = _CYAN if self._selected else _CYAN_DIM
        ca = QColor(c.red(), c.green(), c.blue(), 40)
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.15, ca)
        grad.setColorAt(0.5, c)
        grad.setColorAt(0.85, ca)
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(bar, 1, 1)

        for x_off in (0.2, 0.8):
            fx = rc.x() + 8 + (rc.width() - 16) * x_off
            p.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 50), 1))
            p.drawLine(QPointF(fx, bar.bottom() + 1), QPointF(fx, rc.bottom() - 3))

        if self._selected:
            self._draw_wireframe(p, rc)

    def _draw_wireframe(self, p: QPainter, rc: QRectF) -> None:
        ang = math.radians(self._wire_angle)
        margin = 2.5 + 1.2 * math.sin(ang * 2)
        r = rc.adjusted(margin, margin, -margin, -margin)

        pen = QPen(_ORANGE, 1.6)
        pen.setStyle(Qt.DashLine)
        pen.setDashPattern([4, 3])
        pen.setDashOffset(self._wire_angle * 0.5)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r, 5, 5)

        bracket = 8
        pen2 = QPen(_ORANGE, 2.0)
        pen2.setStyle(Qt.SolidLine)
        p.setPen(pen2)
        corners = [
            (r.left(), r.top(),     1,  1),
            (r.right(), r.top(),   -1,  1),
            (r.left(), r.bottom(),  1, -1),
            (r.right(), r.bottom(),-1, -1),
        ]
        for bx, by, dx, dy in corners:
            p.drawLine(QPointF(bx, by), QPointF(bx + dx * bracket, by))
            p.drawLine(QPointF(bx, by), QPointF(bx, by + dy * bracket))
        p.setBrush(_ORANGE)
        for bx, by, _, _ in corners:
            p.drawEllipse(QPointF(bx, by), 1.8, 1.8)

    # -- events --------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.pet_type)

    # -- selection property --------------------------------------------------

    @pyqtProperty(float)
    def hl(self) -> float:
        return 1.0 if self._selected else 0.0

    @hl.setter
    def hl(self, val: float) -> None:
        self._selected = val > 0.5
        self.update()

    def set_selected(self, val: bool) -> None:
        self._hl_anim.stop()
        self._hl_anim.setStartValue(1.0 if self._selected else 0.0)
        self._hl_anim.setEndValue(1.0 if val else 0.0)
        self._selected = val
        self._hl_anim.start()
        self.update()


# ---------------------------------------------------------------------------
# Background grid
# ---------------------------------------------------------------------------
def _draw_perspective_grid(p: QPainter, rect: QRect, time: float) -> None:
    w, h   = rect.width(), rect.height()
    cx     = w / 2
    bottom = float(h)
    p.setRenderHint(QPainter.Antialiasing)

    for i in range(18):
        angle = math.radians(i * 20 + time * 0.3)
        dx = math.sin(angle) * w * 0.9
        dy = -math.cos(angle) * h * 0.7
        clr = QColor(_GRID_LINE)
        clr.setAlpha(int(25 + 20 * math.sin(angle + time)))
        pen = QPen(clr, 1)
        pen.setStyle(Qt.DotLine if i % 2 else Qt.SolidLine)
        p.setPen(pen)
        p.drawLine(QPointF(cx, bottom), QPointF(cx + dx, bottom + dy))

    for i in range(1, 15):
        tv = i / 14
        y  = bottom - tv * h * 0.78 + 8 * math.sin(time + i * 0.5)
        alpha = max(5, int(45 * (1 - tv)))
        pen = QPen(QColor(0, 200, 230, alpha), 1)
        pen.setStyle(Qt.DotLine if i % 3 == 0 else Qt.SolidLine)
        p.setPen(pen)
        spread = w * 0.15 + w * 0.35 * (1 - tv)
        p.drawLine(QPointF(cx - spread, y), QPointF(cx + spread, y))

    p.setBrush(Qt.NoBrush)
    for r in [4, 8, 14]:
        p.setPen(QPen(QColor(0, 230, 255, max(5, 40 - r * 2)), 1))
        p.drawEllipse(QPointF(cx, bottom), r, r)


# ---------------------------------------------------------------------------
# SettingsWindow
# ---------------------------------------------------------------------------
class SettingsWindow(QWidget):
    def __init__(self, pet, pet_window=None) -> None:
        super().__init__()
        self.pet        = pet
        self.pet_window = pet_window
        self._selected_type: str      = pet.pet_type
        self._cards: dict[str, HologramCard] = {}
        self._drag_pos: QPoint | None = None
        self._closing    = False
        self._anim_time  = 0.0
        self._bg_tick    = 0
        self._grid_cache: QPixmap | None = None

        self.setWindowOpacity(0.0)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(50)

        self._build()

    # -- construction --------------------------------------------------------

    def _build(self) -> None:
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(_W, _H)
        self.setStyleSheet(_CSS)

        scr = QApplication.desktop().availableGeometry()
        self.move(
            scr.left() + (scr.width()  - _W) // 2,
            scr.top()  + (scr.height() - _H) // 2,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_title_bar())
        root.addWidget(self._make_content())

    def _make_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(_TITLE_H)
        bar.setStyleSheet(
            f"background:rgba(8,10,20,200); border-radius:{_RADIUS}px {_RADIUS}px 0 0;"
        )
        row = QHBoxLayout(bar)
        row.setContentsMargins(22, 0, 12, 0)

        self._title_lbl = GlowLabel(t("sw_title"), _CYAN, 13, bold=True, blur=16, tracking=3)
        row.addWidget(self._title_lbl)
        row.addStretch()

        cls_btn = QPushButton("✕")
        cls_btn.setObjectName("cls")
        cls_btn.setFixedSize(30, 30)
        cls_btn.clicked.connect(self._close_animated)
        row.addWidget(cls_btn)
        return bar

    def _make_content(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(
            "background:rgba(12,15,30,220);"
            f" border-radius:0 0 {_RADIUS}px {_RADIUS}px;"
        )
        col = QVBoxLayout(panel)
        col.setContentsMargins(24, 12, 24, 18)
        col.setSpacing(0)

        # -- PET section (scrollable 3-col grid) ----------------------------
        self._section_pet_lbl = _section_label(t("sw_pet"))
        col.addWidget(self._section_pet_lbl)
        col.addSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(190)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 2, 0, 2)
        inner_lay.setSpacing(0)

        center_row = QHBoxLayout()
        center_row.setContentsMargins(0, 0, 0, 0)
        center_row.addStretch()
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)
        for idx, pt in enumerate(_PET_TYPES):
            card = HologramCard(
                pt, t(f"card_{pt}"),
                _idle_sprite(pt),
                pt == self._selected_type,
            )
            card.clicked.connect(self._select_card)
            self._cards[pt] = card
            grid.addWidget(card, idx // 3, idx % 3)
        center_row.addLayout(grid)
        center_row.addStretch()
        inner_lay.addLayout(center_row)
        inner_lay.addStretch()

        scroll.setWidget(inner)
        col.addWidget(scroll)
        col.addSpacing(12)

        # -- NAME section ---------------------------------------------------
        self._section_name_lbl = _section_label(t("sw_name"))
        col.addWidget(self._section_name_lbl)
        col.addSpacing(5)

        self.name_input = QLineEdit(self.pet.name)
        self.name_input.setPlaceholderText(t("sw_name_ph"))
        self.name_input.setFixedHeight(38)
        col.addWidget(self.name_input)
        col.addSpacing(12)

        # -- LANGUAGE section -----------------------------------------------
        self._section_lang_lbl = _section_label(t("sw_language"))
        col.addWidget(self._section_lang_lbl)
        col.addSpacing(5)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(10)

        self._lang_ru_btn = QPushButton(t("sw_lang_ru"))
        self._lang_ru_btn.setFixedHeight(34)
        self._lang_ru_btn.setCursor(Qt.PointingHandCursor)
        self._lang_ru_btn.clicked.connect(lambda: self._set_language("ru"))
        lang_row.addWidget(self._lang_ru_btn)

        self._lang_en_btn = QPushButton(t("sw_lang_en"))
        self._lang_en_btn.setFixedHeight(34)
        self._lang_en_btn.setCursor(Qt.PointingHandCursor)
        self._lang_en_btn.clicked.connect(lambda: self._set_language("en"))
        lang_row.addWidget(self._lang_en_btn)

        col.addLayout(lang_row)
        self._update_lang_buttons(get_lang())
        col.addSpacing(12)

        # -- ACTIVE PETS section --------------------------------------------
        self._section_pets_lbl = _section_label(t("sw_active_pets"))
        col.addWidget(self._section_pets_lbl)
        col.addSpacing(5)

        self._pets_container = QWidget()
        self._pets_container.setStyleSheet("background:transparent;")
        self._pets_body = QVBoxLayout(self._pets_container)
        self._pets_body.setContentsMargins(0, 0, 0, 0)
        self._pets_body.setSpacing(4)

        pets_scroll = QScrollArea()
        pets_scroll.setWidget(self._pets_container)
        pets_scroll.setWidgetResizable(True)
        pets_scroll.setFixedHeight(96)
        pets_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pets_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        col.addWidget(pets_scroll)
        self._rebuild_pets_section()

        col.addStretch()

        # -- bottom buttons -------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._cancel_btn = QPushButton(t("sw_cancel"))
        self._cancel_btn.setObjectName("cancel")
        self._cancel_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._close_animated)
        self._cancel_btn.setFixedHeight(38)
        btn_row.addWidget(self._cancel_btn)

        self._add_btn = QPushButton(t("sw_add_pet"))
        self._add_btn.setObjectName("add_pet_btn_main")
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.clicked.connect(
            lambda: self._add_satellite_from_settings(self._selected_type)
        )
        self._add_btn.setFixedHeight(38)
        btn_row.addWidget(self._add_btn)

        self._apply_btn = QPushButton(t("sw_apply"))
        self._apply_btn.setObjectName("apply")
        self._apply_btn.setCursor(Qt.PointingHandCursor)
        self._apply_btn.clicked.connect(self._apply)
        self._apply_btn.setFixedHeight(38)
        btn_row.addWidget(self._apply_btn)

        col.addLayout(btn_row)
        return panel

    # -- paint ---------------------------------------------------------------

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rc = self.rect().adjusted(0, 0, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rc), _RADIUS, _RADIUS)
        p.setClipPath(path)
        p.fillRect(rc, _BG_DEEP)

        if self._grid_cache is None or self._grid_cache.size() != self.size():
            self._grid_cache = QPixmap(self.size())
            self._grid_cache.fill(Qt.transparent)
            gp = QPainter(self._grid_cache)
            gp.setRenderHint(QPainter.Antialiasing)
            _draw_perspective_grid(gp, rc, self._anim_time)
            gp.end()
        p.drawPixmap(0, 0, self._grid_cache)

        for w, alpha in [(3, 60), (2, 120), (1, 200)]:
            p.setPen(QPen(QColor(0, 210, 240, alpha), w))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(rc), _RADIUS, _RADIUS)

    # -- animation -----------------------------------------------------------

    def _tick_anim(self) -> None:
        self._anim_time += 0.05          # same speed: 1 unit/s at 50 ms interval
        self._bg_tick = (self._bg_tick + 1) % 2

        for card in self._cards.values():
            if card._selected:
                card._wire_angle = (card._wire_angle + 1.5) % 360   # 30°/s
                card.update()

        if self._bg_tick == 0:           # full window repaint at ~10 fps
            self._grid_cache = None
            self.update()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._closing = False
        self._grid_cache = None
        target = self.pos()

        self._anim_fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim_fade.setDuration(260)
        self._anim_fade.setStartValue(0.0)
        self._anim_fade.setEndValue(1.0)
        self._anim_fade.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_slide = QPropertyAnimation(self, b"pos", self)
        self._anim_slide.setDuration(260)
        self._anim_slide.setStartValue(target + QPoint(0, 16))
        self._anim_slide.setEndValue(target)
        self._anim_slide.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_fade.start()
        self._anim_slide.start()

    def _close_animated(self) -> None:
        if self._closing:
            return
        self._closing = True
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(180)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self._anim_timer.stop)
        anim.finished.connect(self.close)
        self._anim_out = anim
        anim.start()

    # -- drag ----------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, _) -> None:
        self._drag_pos = None

    # -- language ------------------------------------------------------------

    def _update_lang_buttons(self, active: str) -> None:
        on = (
            f"color:{_ACCENT_CYAN}; border:1.5px solid {_ACCENT_CYAN};"
            f" background:rgba(0,230,255,22); border-radius:8px;"
            f" font-weight:bold; font-size:12px; letter-spacing:1px; padding:0;"
        )
        off = (
            f"color:rgba(0,180,210,90); border:1px solid rgba(0,180,210,45);"
            f" background:rgba(0,230,255,4); border-radius:8px;"
            f" font-weight:bold; font-size:12px; letter-spacing:1px; padding:0;"
        )
        self._lang_ru_btn.setStyleSheet(on if active == "ru" else off)
        self._lang_en_btn.setStyleSheet(on if active == "en" else off)

    def _set_language(self, lang: str) -> None:
        if lang == get_lang():
            return
        save_lang(lang)          # sets _current_lang + persists to registry
        primary = self._get_primary_window()
        if primary:
            primary.tray.setContextMenu(primary._build_tray_menu())
        self._refresh_text()

    def _refresh_text(self) -> None:
        self._title_lbl.setText(t("sw_title"))
        self._section_pet_lbl.setText(t("sw_pet"))
        self._section_name_lbl.setText(t("sw_name"))
        self._section_lang_lbl.setText(t("sw_language"))
        self._section_pets_lbl.setText(t("sw_active_pets"))
        self._add_btn.setText(t("sw_add_pet"))
        self.name_input.setPlaceholderText(t("sw_name_ph"))
        self._cancel_btn.setText(t("sw_cancel"))
        self._apply_btn.setText(t("sw_apply"))
        for pt in _PET_TYPES:
            if pt in self._cards:
                self._cards[pt].set_display_name(t(f"card_{pt}"))
        self._update_lang_buttons(get_lang())
        self._rebuild_pets_section()

    # -- add / active pets ---------------------------------------------------

    def _get_primary_window(self):
        if self.pet_window is None:
            return None
        return self.pet_window if self.pet_window._is_primary else self.pet_window._manager

    def _get_satellites(self) -> list:
        primary = self._get_primary_window()
        return list(primary._satellites) if primary else []

    def _add_satellite_from_settings(self, pet_type: str) -> None:
        primary = self._get_primary_window()
        if primary:
            primary._add_satellite(pet_type)
            self._rebuild_pets_section()

    def _rebuild_pets_section(self) -> None:
        while self._pets_body.count():
            item = self._pets_body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        satellites = self._get_satellites()
        if not satellites:
            lbl = QLabel(t("sw_no_extra"))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "color:rgba(0,180,210,55); font-size:11px; background:transparent;"
            )
            self._pets_body.addWidget(lbl)
            return

        for sat in satellites:
            row_w = QWidget()
            row_w.setStyleSheet("background:transparent;")
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(2, 0, 2, 0)
            row_lay.setSpacing(8)

            emoji = _PET_EMOJI.get(sat.pet.pet_type, "🐾")
            name_lbl = QLabel(f"{emoji}  {sat.pet.name}")
            name_lbl.setStyleSheet(
                f"color:{_ACCENT_CYAN}; font-size:12px; background:transparent;"
            )
            row_lay.addWidget(name_lbl)
            row_lay.addStretch()

            rm_btn = QPushButton(t("remove_pet"))
            rm_btn.setObjectName("rm")
            rm_btn.setFixedHeight(24)
            rm_btn.setCursor(Qt.PointingHandCursor)
            rm_btn.clicked.connect(lambda checked=False, s=sat: self._remove_satellite(s))
            row_lay.addWidget(rm_btn)

            self._pets_body.addWidget(row_w)

    def _remove_satellite(self, sat) -> None:
        sat._remove_self()
        self._rebuild_pets_section()

    # -- card selection ------------------------------------------------------

    def _select_card(self, pet_type: str) -> None:
        if pet_type == self._selected_type:
            return
        self._cards[self._selected_type].set_selected(False)
        self._selected_type = pet_type
        self._cards[pet_type].set_selected(True)

    # -- apply ---------------------------------------------------------------

    def _apply(self) -> None:
        new_name = self.name_input.text().strip() or self.pet.name
        new_type = self._selected_type
        if self.pet_window:
            if new_type != self.pet.pet_type:
                self.pet_window.set_pet_type(new_type, new_name)
                save_pet(new_type)
            elif new_name != self.pet.name:
                self.pet.name = new_name
                self.pet.save_state()
        self._close_animated()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _idle_sprite(pet_type: str) -> QPixmap:
    path = resource_base() / "assets" / "sprites" / pet_type / "idle" / "frame_1.png"
    px = QPixmap(str(path))
    if not px.isNull():
        return px
    px = QPixmap(str(resource_base() / "assets" / "icons" / f"{pet_type}.ico"))
    if not px.isNull():
        return px
    return QPixmap()
