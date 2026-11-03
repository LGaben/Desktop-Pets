"""Measure one isolated Qt scenario; offscreen results exclude DWM rendering."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback


def process_memory() -> dict[str, int | None]:
    """Current process RSS/private bytes, using the standard Windows API."""
    if os.name != "nt":
        return {"rss_bytes": None, "private_bytes": None}
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage", "PrivateUsage",
            )
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"rss_bytes": counters.WorkingSetSize, "private_bytes": counters.PrivateUsage}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pets", type=int, choices=(1, 5, 10), required=True)
    parser.add_argument("--state", choices=("idle", "moving", "hidden"), required=True)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--warmup", type=float, default=1.0)
    parser.add_argument("--platform", choices=("offscreen", "windows"), default="offscreen")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seconds <= 0 or args.warmup < 0:
        parser.error("seconds must be positive and warmup nonnegative")

    os.environ["QT_QPA_PLATFORM"] = args.platform
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from PyQt6.QtCore import QCoreApplication, QEvent, QPoint, QTimer
    from PyQt6.QtWidgets import QApplication

    from ui.pet_window import PetWindow
    from utils.geometry import movement_bounds
    from utils.settings_store import store

    class MemoryBackend:
        def read(self):
            return {}

        def write(self, values):
            pass

    store.backend = MemoryBackend()
    store.load()
    random.seed(42)
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    baseline = process_memory()
    primary = PetWindow()
    for _ in range(args.pets - 1):
        primary._add_satellite("fox")
    windows = [primary] + primary._satellites

    def start_walk(window):
        pet = window.pet
        bounds = movement_bounds(pet.position, window.size())
        corners = (bounds.topLeft(), bounds.bottomRight())
        target = max(corners, key=lambda p: (p.x() - pet.position.x()) ** 2 +
                                           (p.y() - pet.position.y()) ** 2)
        pet._walk_target = QPoint(target)
        pet._walk_timer = 1000000
        pet.change_state("walk")

    for window in windows:
        # Keep normal application timers; make each scenario reproducible by
        # suppressing random AI changes rather than disabling its timers.
        window.pet.decide_next_action = lambda: None
        window.pet.tick_mouse_check = lambda: None
        if args.state == "moving":
            start_walk(window)
        else:
            window.pet.change_state("idle")
        if args.state == "hidden":
            window.hide()

    samples = []
    errors = []
    start = {}

    def exception_hook(exc_type, exc, tb):
        errors.append("".join(traceback.format_exception(exc_type, exc, tb)))
        app.exit(1)

    sys.excepthook = exception_hook

    def sample():
        active = sum(timer.isActive() for window in windows for timer in
                     (window._animation_timer, window._state_timer,
                      window._behavior_timer, window._mouse_timer))
        samples.append({"elapsed": time.perf_counter() - start["wall"],
                        "active_pet_timers": active,
                        "moving_pets": sum(window.pet.is_moving for window in windows),
                        **process_memory()})
        if args.state == "hidden" and active:
            raise AssertionError(f"Hidden pets still have {active} active timers")
        if args.state == "moving":
            for window in windows:
                if not window.pet.is_moving:
                    start_walk(window)

    sampler = QTimer()
    sampler.setInterval(200)
    sampler.timeout.connect(sample)

    def finish():
        sample()
        elapsed = time.perf_counter() - start["wall"]
        cpu = time.process_time() - start["cpu"]
        result = {
            "pets": args.pets, "state": args.state, "qt_platform": app.platformName(),
            "includes_dwm_rendering": False,
            "measurement_scope": "Qt process only; compositor/GPU costs are excluded",
            "sampler_interval_ms": 200,
            "behavior_control": "Random AI suppressed; normal pet timers retained",
            "wall_seconds": elapsed, "cpu_seconds": cpu,
            "cpu_percent_one_core": 100 * cpu / elapsed,
            "baseline_memory": baseline, "samples": samples,
            "max_active_pet_timers": max(row["active_pet_timers"] for row in samples),
            "max_rss_bytes": max((row["rss_bytes"] for row in samples
                                  if row["rss_bytes"] is not None), default=None),
            "max_private_bytes": max((row["private_bytes"] for row in samples
                                      if row["private_bytes"] is not None), default=None),
            "errors": errors,
        }
        for name in ("rss", "private"):
            value = result[f"max_{name}_bytes"]
            result[f"max_{name}_mib"] = value / (1024 ** 2) if value is not None else None
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({key: result[key] for key in
                          ("pets", "state", "cpu_percent_one_core", "max_rss_bytes",
                           "max_private_bytes", "max_active_pet_timers", "qt_platform")}))
        sampler.stop()
        primary._shutdown()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.exit(bool(errors))

    def begin():
        start.update(wall=time.perf_counter(), cpu=time.process_time())
        sample()
        sampler.start()
        QTimer.singleShot(round(args.seconds * 1000), finish)

    QTimer.singleShot(round(args.warmup * 1000), begin)
    code = app.exec()
    primary._shutdown()
    if errors:
        print("\n".join(errors), file=sys.stderr)
    return int(code or bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
