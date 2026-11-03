"""Run isolated Qt event journeys at 100/150/200 percent and save exact evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    sys.path.insert(0, str(ROOT))
    from scripts.build_release import source_manifest
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, default=ROOT / '.build-envs/qt6-cp313/Scripts/python.exe')
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report = ROOT / 'reports/verification' / f'{stamp}-menu-e2e'
    report.mkdir(parents=True)
    snapshot = source_manifest()
    (report / 'source-manifest.json').write_text(json.dumps(snapshot, indent=2), encoding='utf8')
    summary = {'status': 'running', 'live_app_tested': False, 'python': str(args.python),
               'source_sha256': snapshot['sha256'], 'steps': []}

    def save():
        (report / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')

    def run(name, command, env):
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                    timeout=240)
            output, code = result.stdout, result.returncode
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout or b''
            if isinstance(partial, bytes):
                partial = partial.decode('utf-8', errors='replace')
            output, code = partial + '\n' + str(exc), None
        except OSError as exc:
            output, code = str(exc), None
        (report / f'{name}.log').write_text(output, encoding='utf8')
        summary['steps'].append({'name': name, 'command': command, 'exit_code': code})
        save()
        return code == 0

    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_SCALE_FACTOR='1',
                       PYTHONUTF8='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    environment.pop('PET_MENU_E2E_OUTPUT', None)
    probe = [str(args.python), '-c', 'import sys, pytest; from PyQt6.QtCore import qVersion; print(sys.version); print(qVersion())']
    if not run('environment', probe, environment):
        summary['status'] = 'blocked'
    else:
        summary['status'] = 'passed'
        for scale in ('1', '1.5', '2'):
            screenshots = report / f'scale-{scale}'
            screenshots.mkdir()
            env = dict(environment, QT_SCALE_FACTOR=scale, PET_MENU_E2E_OUTPUT=str(screenshots))
            command = [str(args.python), '-m', 'pytest', '-q', '-ra',
                       '--junitxml=' + str(report / f'scale-{scale}.xml'),
                       'tests/test_menu_e2e_qt.py', 'tests/test_menu_design_qt.py',
                       'tests/test_menu_cursor_qt.py', 'tests/test_cursor_group_qt.py', 'tests/test_security_qt.py']
            if not run(f'scale-{scale}', command, env):
                summary['status'] = 'failed'
        if summary['status'] == 'passed':
            if not run('full-pytest', [str(args.python), '-m', 'pytest', '-q', '-ra'], environment):
                summary['status'] = 'failed'
    summary['source_unchanged'] = source_manifest() == snapshot
    if not summary['source_unchanged']:
        summary['status'] = 'failed'
    save()
    print(f"Menu E2E: {summary['status']}. Logs and PNG: {report}")
    print('This tests isolated source windows, not the already-running EXE.')
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
