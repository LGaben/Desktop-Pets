"""Fail-closed package locks and bounded non-executing bundle inspection."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from scripts.verify_bundle import MAGIC, MAX_DLL_BYTES, archive_entries, entry_bytes
from scripts.verify_lock import PROVENANCE, ROOT, validate


class ReleaseSecurityTests(unittest.TestCase):
    def test_reviewed_wheels_match_target_and_observed_dependency_constraints(self):
        data = validate(ROOT / 'requirements/test-cp313-win_amd64.lock')
        self.assertEqual(data['pinned_wheels'], 18)
        self.assertEqual(set(data['dependency_metadata_not_observed']), {'pyqt6-sip', 'ruff'})
        self.assertFalse(data['pip_resolution_executed'])

    def test_changed_hash_or_wrong_platform_fails_validation(self):
        original = json.loads(PROVENANCE.read_text())
        for key, value in (('sha256', '0' * 64), ('filename', 'pyqt6-6.12.0-cp310-abi3-win_arm64.whl')):
            data = json.loads(json.dumps(original))
            next(item for item in data['packages'] if item['name'] == 'PyQt6')[key] = value
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'provenance.json'
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    validate(ROOT / 'requirements/test-cp313-win_amd64.lock', path)

    def test_synthetic_archive_only_reads_declared_entry_as_bytes(self):
        content = b'not executable; parser data only'
        payload = zlib.compress(content)
        name = b'Qt6Core.dll\0'
        toc = struct.pack('!IIIIBc', 18 + len(name), 0, len(payload), len(content), 1, b'b') + name
        size = len(payload) + len(toc) + 88
        cookie = struct.pack('!8sIIII64s', MAGIC, size, len(payload), len(toc), 313, b'python313.dll')
        blob = b'prefix' + payload + toc + cookie
        tag, library, entries = archive_entries(blob)
        self.assertEqual((tag, library), (313, 'python313.dll'))
        self.assertEqual(entry_bytes(blob, entries['Qt6Core.dll']), b'not executable; parser data only')

    def test_corrupt_and_oversized_entries_are_rejected(self):
        with self.assertRaises(ValueError):
            archive_entries(b'not an archive')
        with self.assertRaises(ValueError):
            entry_bytes(b'x', (0, 1, MAX_DLL_BYTES + 1, 0, b'b'))
        with self.assertRaises(ValueError):
            entry_bytes(zlib.compress(b'abc'), (0, 11, 2, 1, b'b'))


if __name__ == '__main__':
    unittest.main()
