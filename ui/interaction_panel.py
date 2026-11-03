"""Single-level native menus with a painted panel and adaptive ring layout."""
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QSizePolicy, QStyle, QStyleOptionButton, QVBoxLayout, QWidget)

from ui.menu_style import inline_menu_style
from ui.menu_visuals import action_icon, colors, menu_stylesheet
from utils.geometry import available_rect, clamp_position
from utils.i18n import t


class NameLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        text = self.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), text)


class MenuSurface(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(colors()['line']))
        painter.setBrush(QColor(colors()['surface']))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)


class InteractionPanel(QFrame):
    def __init__(self, parent, title, character, actions, style='panel', portrait=None, style_changed=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName('interactionPanel')
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFont(QFont('Segoe UI', 10))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.menu_style = style
        self._title, self._character, self._actions = title, character, actions
        self._portrait, self._style_changed = portrait, style_changed
        self._radial = style == 'ring'
        self._compact = False
        self._action_buttons = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._scroll = QScrollArea(self)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidgetResizable(True)
        self._scroll.viewport().setAutoFillBackground(False)
        layout.addWidget(self._scroll)
        self._build_content()

    def paintEvent(self, event):
        if not self._radial or self._compact:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QColor(colors()['line']))
            painter.setBrush(QColor(colors()['surface']))
            painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 16, 16)

    def _button(self, label, callback, parent, radial=False):
        button = QPushButton(label, parent)
        button.setAccessibleName(label)
        button.setIcon(action_icon(label))
        button.setIconSize(QSize(20, 20))
        button.setMinimumHeight(56 if radial else 44)
        button.setMinimumWidth(button.fontMetrics().horizontalAdvance(label) + 20 + 6 + 26)
        button.clicked.connect(lambda checked=False: self._activate(callback))
        if radial:
            button.setObjectName('ringAction')
            button.setFixedHeight(max(56, button.fontMetrics().height() + 20))
        self._action_buttons.append(button)
        return button

    def _build_content(self):
        old = self._scroll.takeWidget()
        if old:
            old.setParent(None)
            old.deleteLater()
        self._action_buttons = []
        ring = self._radial and not self._compact
        self.setProperty('radial', ring)
        self.setStyleSheet(menu_stylesheet())
        body = QWidget()
        body.setObjectName('petActions')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        settings = next((call for label, call in self._actions if label == t('settings')), None)
        header = QPushButton() if ring and settings else QWidget()
        header.setObjectName('petProfile' if ring else 'panelProfile')
        header_layout = QVBoxLayout(header) if ring else QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(2 if ring else 8)
        if self._portrait is not None and not self._portrait.isNull():
            portrait = QLabel(header)
            portrait.setObjectName('petPortrait')
            side = 32 if ring else 40
            portrait.setPixmap(self._portrait.scaled(side, side, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.FastTransformation))
            header_layout.addWidget(portrait, alignment=Qt.AlignmentFlag.AlignCenter)
        identity = QWidget(header)
        identity_layout = QVBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(0)
        heading = NameLabel()
        heading.setObjectName('petName')
        heading.setTextFormat(Qt.TextFormat.PlainText)
        heading.setText(self._title)
        heading.setAccessibleName(self._title)
        heading.setMinimumHeight(20)
        heading.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        identity_layout.addWidget(heading)
        if self._character and not ring:
            badge = NameLabel()
            badge.setObjectName('petCharacter')
            badge.setTextFormat(Qt.TextFormat.PlainText)
            badge.setText(self._character)
            badge.setMinimumHeight(20)
            badge.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            identity_layout.addWidget(badge)
        header_layout.addWidget(identity, 1)
        if ring and settings:
            header.setAccessibleName(t('settings'))
            header.clicked.connect(lambda checked=False: self._activate(settings))
            caption = QLabel(t('settings'))
            caption.setObjectName('petCharacter')
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(caption)
            for child in header.findChildren(QWidget):
                child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        elif settings:
            shortcut = self._button(t('settings'), settings, header)
            shortcut.setText('')
            shortcut.setMinimumWidth(44)
            shortcut.setFixedSize(44, 44)
            shortcut.setObjectName('settingsShortcut')
            shortcut.setToolTip(t('settings'))
            header_layout.addWidget(shortcut)
        primary_keys = ('pet_action', 'ball_action', 'sleep', 'wake_up')
        primary = [(label, call) for label, call in self._actions if label in {t(key) for key in primary_keys}]
        others = [(label, call) for label, call in self._actions
                  if label != t('settings') and label not in {item[0] for item in primary}]
        if ring:
            grid = QGridLayout()
            grid.setSpacing(8)
            header.setMinimumSize(112, 100)
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            positions = ((0, 1), (1, 0), (1, 2))
            for index, (label, call) in enumerate(primary):
                if index < len(positions):
                    grid.addWidget(self._button(label, call, body, True), *positions[index])
                else:
                    others.append((label, call))
            layout.addLayout(grid)
        else:
            header.setMinimumHeight(60)
            layout.addWidget(header)
            for label, call in primary:
                layout.addWidget(self._button(label, call, body))
        footer = MenuSurface(body) if ring else QWidget(body)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(8 if ring else 0, 8 if ring else 0, 8 if ring else 0, 8 if ring else 0)
        footer_layout.setSpacing(4)
        service_keys = ('hide_to_tray', 'remove_pet', 'quit')
        services = []
        for label, call in others:
            if label in {t(key) for key in service_keys}:
                services.append((label, call))
            else:
                footer_layout.addWidget(self._button(label, call, footer))
        if self._style_changed is not None:
            footer_layout.addWidget(inline_menu_style(self.menu_style, self._style_changed, footer))
        for label, call in services:
            footer_layout.addWidget(self._button(label, call, footer))
        layout.addWidget(footer)
        self._scroll.setWidget(body)

    def _activate(self, callback):
        self.close()
        callback()

    def open_at(self, point):
        bounds = available_rect(point)
        self.ensurePolished()
        hint = self._content_hint()
        if self._radial and (hint.width() + 16 > bounds.width() or hint.height() + 16 > bounds.height()):
            self._compact = True
            self._build_content()
            hint = self._content_hint()
        self.resize(min(hint.width() + 16, bounds.width()), min(hint.height() + 16, bounds.height()))
        self.move(clamp_position(point, self.size(), bounds))
        self.show()
        if self._radial and not self._compact:
            self.layout().activate()
            self._scroll.widget().layout().activate()
            profile = self.findChild(QWidget, 'petProfile')
            anchor = point - profile.mapTo(self, profile.rect().center())
            self.move(clamp_position(anchor, self.size(), bounds))
        if self._actions:
            next(button for button in self._action_buttons
                 if button.accessibleName() == self._actions[0][0]).setFocus()

    def _content_hint(self):
        body = self._scroll.widget()
        body.ensurePolished()
        # The detached body only inherits the popup font after setWidget().
        for button in body.findChildren(QPushButton):
            if button.objectName() in ('settingsShortcut', 'petProfile'):
                continue
            button.ensurePolished()
            option = QStyleOptionButton()
            option.initFrom(button)
            option.text, option.icon, option.iconSize = button.text(), button.icon(), button.iconSize()
            content = QSize(button.fontMetrics().horizontalAdvance(button.text()), button.fontMetrics().height())
            if not button.icon().isNull():
                content.setWidth(content.width() + button.iconSize().width() + 4)
                content.setHeight(max(content.height(), button.iconSize().height()))
            required = button.style().sizeFromContents(QStyle.ContentsType.CT_PushButton, option, content, button)
            button.setMinimumWidth(max(44, required.width()))
            if button.objectName() == 'ringAction':
                button.setFixedHeight(max(56, required.height()))
            else:
                button.setMinimumHeight(max(44, required.height()))
        body.layout().activate()
        hint = body.sizeHint().expandedTo(body.minimumSizeHint())
        if not self._radial or self._compact:
            hint.setWidth(max(256, hint.width()))
        return hint

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
