"""The same global menu-style selector in the tray and pet's More menu."""
from PyQt6.QtGui import QActionGroup
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from utils.i18n import t
from utils.settings_store import MENU_STYLES


def inline_menu_style(current, callback, parent=None):
    selector = QWidget(parent)
    selector.setAccessibleName(t('menu_style'))
    layout = QHBoxLayout(selector)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    group = QButtonGroup(selector)
    group.setExclusive(True)
    for style in MENU_STYLES:
        button = QPushButton(t(f'menu_{style}'), selector)
        button.setObjectName('menuStyleOption')
        button.setProperty('menuStyle', style)
        button.setAccessibleName(f"{t('menu_style')}: {t(f'menu_{style}')}")
        button.setMinimumHeight(44)
        button.setMinimumWidth(button.fontMetrics().horizontalAdvance(button.text()) + 28)
        button.setCheckable(True)
        button.setChecked(current == style)
        group.addButton(button)
        button.clicked.connect(lambda checked=False, value=style: callback(value))
        layout.addWidget(button)
    return selector


def add_menu_style(menu, window):
    submenu = menu.addMenu(t('menu_style'))
    group = QActionGroup(submenu)
    group.setExclusive(True)
    for style in MENU_STYLES:
        action = submenu.addAction(t(f'menu_{style}'))
        action.setCheckable(True)
        action.setData(style)
        action.setChecked(window.settings_store.menu_style == style)
        group.addAction(action)
        action.triggered.connect(lambda checked=False, value=style: window._set_menu_style(value))
    return submenu
