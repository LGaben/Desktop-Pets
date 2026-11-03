"""Validate the checked-in Windows CPython 3.13 wheel pins without downloading."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / 'requirements/windows-cp313-amd64.provenance.json'


def read_lock(path, seen=None):
    path = Path(path).resolve()
    seen = set() if seen is None else seen
    if path in seen:
        raise ValueError(f'Duplicate or cyclic lock include: {path.name}')
    seen.add(path)
    pins = {}
    for raw in path.read_text(encoding='utf8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line == '--only-binary=:all:':
            continue
        if line.startswith('-r '):
            included = (path.parent / line[3:]).resolve()
            if not included.is_relative_to(path.parent):
                raise ValueError('Lock include must remain in the requirements directory')
            entries = read_lock(included, seen)
        else:
            match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+) --hash=sha256:([a-f0-9]{64})', line)
            if not match:
                raise ValueError(f'Unpinned/unhashed lock entry: {line}')
            name, version, digest = match.groups()
            entries = {canonicalize_name(name): (version, digest)}
        for name, value in entries.items():
            if name in pins:
                raise ValueError(f'Duplicate pin: {name}')
            pins[name] = value
    return pins


def validate(lock, provenance=PROVENANCE):
    data = json.loads(Path(provenance).read_text(encoding='utf8'))
    pins = read_lock(lock)
    records = {canonicalize_name(item['name']): item for item in data['packages']}
    tags = set(cpython_tags((3, 13), ['cp313'], ['win_amd64']))
    tags.update(compatible_tags((3, 13), 'cp313', ['win_amd64']))
    env = default_environment()
    env.update(python_version='3.13', python_full_version='3.13.9', sys_platform='win32',
               os_name='nt', platform_system='Windows', platform_machine='AMD64',
               implementation_name='cpython', platform_python_implementation='CPython', extra='')
    unobserved = []
    for name, (version, digest) in pins.items():
        item = records.get(name)
        if item is None or (item['version'], item['sha256']) != (version, digest):
            raise ValueError(f'Pin differs from reviewed provenance: {name}')
        if item.get('yanked'):
            raise ValueError(f'Yanked wheel: {name}')
        if item.get('requires_python') and not SpecifierSet(item['requires_python']).contains('3.13.9'):
            raise ValueError(f'Unsupported target Python version: {name}')
        wheel_name, wheel_version, _, wheel_tags = parse_wheel_filename(item['filename'])
        if wheel_name != name or wheel_version != Version(version) or not tags.intersection(wheel_tags):
            raise ValueError(f'Wheel does not match CPython 3.13 AMD64: {name}')
        if item.get('dependency_metadata_observed') is False:
            unobserved.append(name)
        for text in item.get('requires_dist') or []:
            dependency = Requirement(text)
            if dependency.marker is not None and not dependency.marker.evaluate(env):
                continue
            target = canonicalize_name(dependency.name)
            if target not in pins or not dependency.specifier.contains(pins[target][0]):
                raise ValueError(f'Missing/incompatible dependency for {name}: {text}')
    return {'target': data['target'], 'pinned_wheels': len(pins),
            'dependency_metadata_not_observed': unobserved,
            'pip_resolution_executed': False,
            'next_check': 'Install with --require-hashes WITHOUT --no-deps, then pip check.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', type=Path, default=ROOT / 'requirements/test-cp313-win_amd64.lock')
    args = parser.parse_args()
    print(json.dumps(validate(args.lock), indent=2))


if __name__ == '__main__':
    main()
