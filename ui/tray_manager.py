# -*- coding: utf-8 -*-
"""System-tray management — icon, tooltip, context menu, notifications.

Single responsibility: own everything related to QSystemTrayIcon for the
primary PetWindow.  PetWindow never touches the tray icon directly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from pet.factory import PetFactory
from ui.menu_style import add_menu_style
from ui.menu_visuals import action_icon, menu_stylesheet
from utils.i18n import t
from utils.paths import resource_base

if TYPE_CHECKING:
    from ui.pet_window import PetWindow


class TrayManager:
    """Owns the QSystemTrayIcon for the primary pet window.

    All tray-related concerns live here and nowhere else:
    - Icon creation and per-pet-type resolution
    - Tooltip management
    - Context-menu construction and refresh
    - Activation handler (double-click → show window)
    - Balloon notifications
    """

    def __init__(self, window: "PetWindow") -> None:
        self._window = window
        self._tray_toggle_action: QAction | None = None

        icon = QIcon(str(self._resolve_icon(window.pet.pet_type)))
        QApplication.setWindowIcon(icon)

        self.tray = QSystemTrayIcon(icon, window)
        self.tray.setToolTip(f"Desktop Pet — {window.pet.name}")
        self.tray.activated.connect(self._on_activated)
        self.rebuild_menu()
        self.tray.show()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def rebuild_menu(self) -> None:
        """Reconstruct and install the context menu from current state."""
        previous = self.tray.contextMenu()
        self._menu = self._build_menu()
        self.tray.setContextMenu(self._menu)
        if previous is not None:
            previous.deleteLater()

    def update_tooltip(self, name: str) -> None:
        """Sync the tray tooltip after a pet name change."""
        self.tray.setToolTip(f"Desktop Pet — {name}")

    def set_toggle_text(self, pet_visible: bool) -> None:
        """Update the Show/Hide label to reflect current window visibility."""
        if self._tray_toggle_action is not None:
            self._tray_toggle_action.setText(
                t("hide_pet") if pet_visible else t("show_pet")
            )

    def show_hidden_message(self) -> None:
        """Display a balloon notification that the pet was minimised."""
        self.tray.showMessage(
            t("tray_hide_title"),
            t("tray_hide_msg"),
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_icon(self, pet_type: str):
        specific = resource_base() / "assets" / "icons" / f"{pet_type}_ico.ico"
        return specific if specific.exists() else (
            resource_base() / "assets" / "icons" / "fox_ico.ico"
        )

    def _on_activated(self, reason: int) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._window._toggle_visibility()

    def _build_menu(self) -> QMenu:
        w = self._window
        menu = QMenu()
        menu.setStyleSheet(menu_stylesheet())

        info = QAction(w.pet.name, menu)
        info.setEnabled(False)
        menu.addAction(info)
        menu.addSeparator()

        self._tray_toggle_action = QAction(t("hide_pet") if w.isVisible() else t("show_pet"), menu)
        self._tray_toggle_action.triggered.connect(w._toggle_visibility)
        menu.addAction(self._tray_toggle_action)

        any_visible = w.isVisible() or any(s.isVisible() for s in w._satellites)
        hide_all = QAction(t("hide_all") if any_visible else t("show_all"), menu)
        hide_all.triggered.connect(w._toggle_all_visibility)
        menu.addAction(hide_all)

        settings_action = QAction(t("settings"), menu)
        settings_action.setIcon(action_icon(t('settings')))
        settings_action.triggered.connect(w._show_settings)
        menu.addAction(settings_action)
        add_menu_style(menu, w)

        pets_menu = menu.addMenu(t('pets_actions'))
        for index, window in enumerate([w] + w._satellites, 1):
            if window._disposed:
                continue
            pet_menu = pets_menu.addMenu(f'{index}. {window.pet.name}')
            for label, callback in window._interaction_actions():
                action = pet_menu.addAction(action_icon(label), label)
                action.triggered.connect(
                    lambda checked=False, target=window, action=callback: target._activate_tray_action(action))

        add_menu = QMenu(t("add_pet"), menu)
        for pt in PetFactory.available_types():
            action = QAction(t(f'card_{pt}'), menu)
            action.triggered.connect(lambda checked=False, p=pt: w._add_satellite(p))
            add_menu.addAction(action)
        menu.addMenu(add_menu)

        menu.addSeparator()
        quit_action = QAction(t("quit"), menu)
        quit_action.triggered.connect(w._quit)
        menu.addAction(quit_action)

        return menu
