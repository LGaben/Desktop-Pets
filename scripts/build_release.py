"""Build an isolated, hash-locked Qt6 release without overwriting existing EXEs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def target_error():
    if (sys.platform != 'win32' or sys.implementation.name != 'cpython'
            or sys.version_info[:2] != (3, 13) or platform.architecture()[0] != '64bit'
            or platform.machine().upper() not in ('AMD64', 'X86_64')
            or not platform.python_compiler().startswith('MSC')):
        return 'Release build requires working Windows CPython 3.13 AMD64 (MSC), not Store aliases or MinGW Python.'
    return None


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def source_manifest():
    files = [ROOT / name for name in ('main.py', 'DesktopPet.spec', 'pyproject.toml', 'requirements.txt')]
    for folder in ('pet', 'ui', 'utils', 'scripts', 'tests'):
        files.extend((ROOT / folder).rglob('*.py'))
    files.extend((ROOT / 'scripts').glob('*.ps1'))
    files.extend((ROOT / 'requirements').glob('*.lock'))
    files.append(ROOT / 'requirements/windows-cp313-amd64.provenance.json')
    files.extend(path for path in (ROOT / 'assets').rglob('*')
                 if path.is_file() and (path.suffix.lower() in ('.png', '.ico') or path.name == '__init__.py'))
    entries = {path.relative_to(ROOT).as_posix(): sha256(path) for path in sorted(set(files))}
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'sha256': digest, 'files': entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Create project venv and install only reviewed hash-locked wheels')
    parser.add_argument('--env', type=Path, default=ROOT / '.build-envs/qt6-cp313')
    parser.add_argument('--sign-thumbprint', help='Optional existing CurrentUser/My code-signing certificate SHA1 thumbprint')
    parser.add_argument('--signtool', type=Path, help='Existing trusted Windows SDK signtool.exe')
    parser.add_argument('--timestamp-url', help='Certificate-provider RFC3161 HTTPS timestamp endpoint')
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report = ROOT / 'reports/verification' / (stamp + '-security-build')
    report.mkdir(parents=True, exist_ok=False)
    originals = (ROOT / 'dist/DesktopPet.exe', ROOT.parent / 'dist/DesktopPet.exe')
    before = {str(path): sha256(path) for path in originals}
    result = {'started': stamp, 'interpreter': sys.executable, 'python': sys.version,
              'compiler': platform.python_compiler(), 'status': 'blocked',
              'old_exe_hashes_before': before, 'steps': [], 'exe_executed': False}
    env = {key: value for key, value in os.environ.items()
           if key not in ('PYTHONPATH', 'PYTHONHOME', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH')}
    env.update(PYTHONNOUSERSITE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', QT_QPA_PLATFORM='offscreen',
               PYTHONIOENCODING='utf-8', PIP_CONFIG_FILE=os.devnull)

    def run(name, command, timeout=900):
        command = [str(value) for value in command]
        completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=timeout,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        (report / (name + '.log')).write_bytes(completed.stdout + b'\n--- stderr ---\n' + completed.stderr)
        result['steps'].append({'name': name, 'command': command, 'exit_code': completed.returncode})
        if completed.returncode:
            raise RuntimeError(f'{name} failed with exit {completed.returncode}; see {report / (name + ".log")}')

    try:
        error = target_error()
        if error:
            raise RuntimeError(error)
        build_env = args.env.resolve()
        if not build_env.is_relative_to(ROOT) or build_env == ROOT:
            raise ValueError('The release environment must be an isolated directory inside this project')
        python = build_env / 'Scripts/python.exe'
        if args.sign_thumbprint:
            if not re.fullmatch('[A-Fa-f0-9]{40}', args.sign_thumbprint):
                raise ValueError('Certificate thumbprint must be exactly 40 hexadecimal characters')
            if not args.signtool or not args.signtool.is_file():
                raise ValueError('Signing requires an existing Windows SDK signtool.exe')
            if not args.timestamp_url or not args.timestamp_url.startswith('https://'):
                raise ValueError('Signing requires a certificate-provider HTTPS RFC3161 timestamp URL')
        if not build_env.exists():
            if not args.install:
                raise RuntimeError('No project build venv; rerun with --install on the supported Python')
            venv.EnvBuilder(with_pip=True).create(build_env)
        if not (build_env / 'pyvenv.cfg').is_file() or not python.is_file():
            raise ValueError('Refusing to install into a directory without a Python venv')
        run('environment-target', [python, '-c',
            "import sys,platform; assert sys.version_info[:2]==(3,13) and sys.platform=='win32'; "
            "assert platform.architecture()[0]=='64bit' and platform.python_compiler().startswith('MSC'); "
            "print(sys.version); print(sys.executable)"])
        lock = ROOT / 'requirements/test-cp313-win_amd64.lock'
        if args.install:
            run('locked-install', [python, '-m', 'pip', '--isolated', '--disable-pip-version-check',
                'install', '--index-url', 'https://pypi.org/simple', '--require-hashes', '--only-binary=:all:',
                '--no-cache-dir', '-r', lock])
        run('pip-check', [python, '-m', 'pip', '--isolated', 'check'])
        run('lock-check', [python, ROOT / 'scripts/verify_lock.py', '--lock', lock])
        run('installed-inventory', [python, '-c',
            "import importlib.metadata as m,json,pathlib; "
            "d=json.loads(pathlib.Path('requirements/windows-cp313-amd64.provenance.json').read_text()); "
            "items={x['name']:m.version(x['name']) for x in d['packages']}; "
            "assert all(items[x['name']]==x['version'] for x in d['packages']); "
            "assert not any(x.metadata['Name'].lower() in ('pyqt5','pyqt5-qt5') for x in m.distributions()); "
            "print(json.dumps(items,indent=2))"])
        snapshot = source_manifest()
        (report / 'source-manifest.json').write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf8')
        result['source_manifest_sha256'] = snapshot['sha256']
        run('compile', [python, '-m', 'compileall', '-q', 'pet', 'ui', 'utils', 'tests', 'scripts', 'main.py'])
        run('pytest', [python, '-m', 'pytest', '-q', '--tb=short', f'--junitxml={report / "pytest.xml"}'])
        dist = ROOT / ('dist-test-security-' + stamp)
        work = ROOT / ('build-test-security-' + stamp)
        if dist.exists() or work.exists():
            raise FileExistsError('Refusing to overwrite a previous build output')
        run('pyinstaller', [python, '-m', 'PyInstaller', ROOT / 'DesktopPet.spec', '--noconfirm',
                           '--distpath', dist, '--workpath', work])
        exe = dist / 'DesktopPet.exe'
        run('bundle-inspection', [python, ROOT / 'scripts/verify_bundle.py', exe, '--output', report / 'bundle.json'])
        if source_manifest() != snapshot:
            raise RuntimeError('Sources changed during verification/build; candidate is not a reviewed release')
        result.update(candidate_exe=str(exe), candidate_sha256=sha256(exe),
                      signing='unsigned; personal certificate not available/requested')
        if args.sign_thumbprint:
            run('sign', [args.signtool, 'sign', '/s', 'My', '/sha1', args.sign_thumbprint,
                         '/fd', 'SHA256', '/tr', args.timestamp_url, '/td', 'SHA256', exe])
            run('verify-signature', [args.signtool, 'verify', '/pa', '/all', '/v', exe])
            run('signed-bundle-inspection', [python, ROOT / 'scripts/verify_bundle.py', exe,
                                             '--output', report / 'signed-bundle.json'])
            result.update(signing='verified with signtool /pa', candidate_sha256=sha256(exe))
        if source_manifest() != snapshot:
            raise RuntimeError('Sources changed before release completion; candidate remains unapproved')
        result['status'] = 'built'
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result['reason'] = str(exc)
    finally:
        result['old_exe_hashes_after'] = {str(path): sha256(path) for path in originals}
        result['old_exes_unchanged'] = result['old_exe_hashes_after'] == before
        (report / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
        print(json.dumps(result, indent=2))
        print(f'Report: {report}')
    return 0 if result['status'] == 'built' and result['old_exes_unchanged'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
