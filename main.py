#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Desktop Pet — entry point."""
import logging
import sys

from PyQt6.QtWidgets import QApplication

from ui.pet_window import PetWindow
from utils.i18n import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)


def main() -> None:
    """Create the Qt application and launch the pet window."""
    load_settings()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _window = PetWindow(restore=True)  # noqa: F841 - retain the top-level window
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
