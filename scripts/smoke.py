"""Offscreen event-loop smoke; never reads/writes the user's settings or DB."""
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QCoreApplication, QEvent, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip
from ui.pet_window import PetWindow
from utils.settings_store import store


class MemoryBackend:
    def __init__(self):
        self.values = {}

    def read(self):
        return dict(self.values)

    def write(self, values):
        self.values = dict(values)


def main():
    store.backend = MemoryBackend()
    store.load()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = PetWindow(restore=True)
    failures = []

    def exercise():
        try:
            window._add_satellite("panda")
            extra = window._satellites[0]
            extra.pet.name = "Smoke Extra"
            extra.pet.save_state()
            extra._throw_ball(extra.x(), extra.y(), extra.x() + 40, extra.y() - 40)
            ball = extra.ball_widget
            extra.hide()
            assert not ball.timer.isActive()
            extra.show()
            extra._show_settings()
            settings = extra.settings_window
            settings._set_language("en")
            settings.name_input.setText("Smoke Dog")
            settings._select_card("dog")
            settings._apply()
            assert not settings._anim_timer.isActive()
            window.hide()
            window.show()
            window._shutdown()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            assert sip.isdeleted(extra)
            assert sip.isdeleted(ball)
            assert sip.isdeleted(settings)
            store.load()
            assert [p["type"] for p in store.roster()] == ["fox", "dog"]
            assert store.roster()[1]["name"] == "Smoke Dog"
        except Exception as exc:
            failures.append(exc)
        finally:
            window._shutdown()
            app.quit()

    QTimer.singleShot(100, exercise)
    app.exec()
    if failures:
        raise failures[0]
    print("PASS: event loop, settings, language, ball cleanup, hide/show, roster")


if __name__ == "__main__":
    main()
