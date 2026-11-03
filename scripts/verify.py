"""Run isolated verification and save logs. Usage: python scripts/verify.py."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-deps", action="store_true",
                        help="Install missing test tools into .verification/deps, never globally")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=float, default=5.0, help="Benchmark duration per scenario")
    parser.add_argument("--skip-benchmark", action="store_true")
    parser.add_argument("--platform", choices=("offscreen", "windows"), default="offscreen",
                        help="windows explicitly shows pet windows; default is noninteractive")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--flake8-path", type=Path,
                        help="Optional existing flake8 package directory for F/E9 fallback")
    args = parser.parse_args()
    if args.seconds <= 0 or args.timeout <= 0:
        parser.error("seconds and timeout must be positive")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or ROOT / "reports" / "verification" / stamp).resolve()
    output.mkdir(parents=True, exist_ok=True)
    runtime_tag = f"{sys.implementation.cache_tag}-{platform.machine()}"
    deps = ROOT / ".verification" / "deps" / runtime_tag
    env = dict(os.environ)
    env.update(QT_QPA_PLATFORM="offscreen", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               PYTHONFAULTHANDLER="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, (
        str(deps), str(args.flake8_path.resolve()) if args.flake8_path else None,
    )))
    exe = ROOT / "dist" / "DesktopPet.exe"
    before = sha256(exe)
    results = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def run(name, command, timeout=None, failure_status="fail"):
        started = time.perf_counter()
        try:
            completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                       timeout=timeout or args.timeout, creationflags=flags)
            code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
            status = "pass" if code == 0 else failure_status
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr, status = None, exc.stdout or b"", exc.stderr or b"", "timeout"
        except OSError as exc:
            code, stdout, stderr, status = None, b"", str(exc).encode("utf-8"), "blocked"
        log = output / f"{name}.log"
        log.write_bytes(stdout + b"\n--- stderr ---\n" + stderr)
        result = {"name": name, "command": command, "status": status, "returncode": code,
                  "seconds": time.perf_counter() - started, "log": str(log)}
        results.append(result)
        print(f"{status.upper():7} {name}: {log}", flush=True)
        return result

    run("pure-tests", [sys.executable, "-m", "unittest", "tests.test_ball_physics",
                       "tests.test_settings_store", "tests.test_storage_isolation",
                       "tests.test_throw_gesture", "tests.test_heart_effect",
                       "tests.test_cursor_reaction", "tests.test_cursor_interest", "-v"])
    run("fox-personality", [sys.executable, "-m", "tests.test_fox_personality"])
    run("compile", [sys.executable, "-m", "compileall", "-q", "pet", "ui", "utils",
                    "tests", "scripts", "main.py"])
    run("runtime-context", [sys.executable, "-c", "import sys,json; "
                            "print(json.dumps({'version':sys.version,'path':sys.path},indent=2))"])

    def probe(module, code):
        result = run(f"probe-{module}", [sys.executable, "-c", code], timeout=20,
                     failure_status="blocked")
        if result["status"] != "pass":
            result["status"] = "blocked"
        return result["status"] == "pass"

    qt = probe("qt", "from PyQt6.QtWidgets import QApplication; from PyQt6.QtCore import "
               "PYQT_VERSION_STR,qVersion; a=QApplication([]); print(PYQT_VERSION_STR,qVersion(),a.platformName())")
    pytest = probe("pytest", "import pytest; print(pytest.__version__)")
    ruff = probe("ruff", "import ruff; print(ruff.__file__)")
    if args.install_deps and not all((qt, pytest, ruff)):
        if (sys.platform != 'win32' or sys.version_info[:2] != (3, 13)
                or platform.architecture()[0] != '64bit' or not platform.python_compiler().startswith('MSC')):
            install = {'name': 'install-deps', 'status': 'blocked',
                       'reason': 'Hash-locked install requires Windows CPython 3.13 AMD64 MSC'}
            results.append(install)
        else:
            install = run('install-deps', [sys.executable, '-m', 'pip', '--isolated',
                          '--disable-pip-version-check', 'install', '--upgrade', '--target', str(deps),
                          '--index-url', 'https://pypi.org/simple', '--require-hashes', '--only-binary=:all:',
                          '--retries', '0', '--timeout', '15', '-r',
                          str(ROOT / 'requirements/test-cp313-win_amd64.lock')], failure_status='blocked')
        if install["status"] == "pass":
            qt = probe("qt-after-install", "from PyQt6.QtWidgets import QApplication; "
                       "a=QApplication([]); print(a.platformName())")
            pytest = probe("pytest-after-install", "import pytest; print(pytest.__version__)")
            ruff = probe("ruff-after-install", "import ruff; print(ruff.__file__)")
            for name, available in (("qt", qt), ("pytest", pytest), ("ruff", ruff)):
                if available:
                    for previous in results:
                        if previous["name"] == f"probe-{name}" and previous["status"] == "blocked":
                            previous["status"] = "superseded"
        else:
            install["status"] = "blocked"

    def blocked(name, reason):
        results.append({"name": name, "status": "blocked", "reason": reason})
        print(f"BLOCKED {name}: {reason}", flush=True)

    if probe('packaging', 'import packaging; print(packaging.__version__)'):
        run('release-security', [sys.executable, '-m', 'unittest', 'tests.test_release_security', '-v'])
        run('wheel-lock', [sys.executable, 'scripts/verify_lock.py'])
    else:
        blocked('release-security', 'Pinned packaging module is required for wheel metadata checks')

    if qt and pytest:
        run("pytest", [sys.executable, "-m", "pytest", "-q", "--tb=short",
                       f"--junitxml={output / 'pytest.xml'}"])
    else:
        blocked("pytest", "Compatible Qt and pytest are required; see probe logs")
    if ruff:
        run("ruff", [sys.executable, "-m", "ruff", "check", "pet", "ui", "utils",
                     "tests", "scripts", "main.py"])
    else:
        blocked("ruff", "ruff is unavailable; use --install-deps in a network-enabled environment")
        if args.flake8_path:
            run("flake8-subset", [sys.executable, "-m", "flake8", "pet", "ui", "utils",
                                  "tests", "scripts", "main.py", "--select", "F,E9"])
    if qt:
        run("smoke", [sys.executable, "scripts/smoke.py"], timeout=45)
    else:
        blocked("smoke", "Qt import/application creation failed")
    if not args.skip_benchmark:
        for count in (1, 5, 10):
            for state in ("idle", "moving", "hidden"):
                name = f"benchmark-{count}-{state}"
                if qt:
                    run(name, [sys.executable, "scripts/benchmark.py", "--pets", str(count),
                               "--state", state, "--seconds", str(args.seconds), "--platform",
                               args.platform, "--output", str(output / f"{name}.json")],
                        timeout=max(30, args.seconds + 15))
                else:
                    blocked(name, "Compatible Qt unavailable; no CPU/memory figures measured")
    after = sha256(exe)
    if before != after:
        results.append({"name": "exe-integrity", "status": "fail",
                        "reason": "EXE hash changed during verification"})
    elif before is None:
        results.append({"name": "exe-integrity", "status": "not-present"})
    else:
        results.append({"name": "exe-integrity", "status": "pass"})
    summary = {"utc": stamp, "python": sys.version, "executable": sys.executable,
               "exe_sha256_before": before, "exe_sha256_after": after,
               "exe_executed": False, "qt_platform": args.platform,
               "dependency_target": str(deps), "pythonpath": env["PYTHONPATH"],
               "results": results}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    failed = any(row["status"] in ("fail", "timeout") for row in results)
    pending = any(row["status"] == "blocked" for row in results)
    print(f"Report: {output / 'summary.json'}", flush=True)
    return 1 if failed else 2 if pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
