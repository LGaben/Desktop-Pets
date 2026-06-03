#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Desktop Pet — entry point."""
import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from ui.pet_window import PetWindow
from utils.i18n import load_settings, get_pet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)


def main() -> None:
    """Create the Qt application and launch the pet window."""
    load_settings()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _window = PetWindow(pet_type=get_pet())  # kept alive by assignment
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
