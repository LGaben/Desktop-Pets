"""Persistence contract tests runnable with unittest without Qt or pytest."""
import json
import unittest
from copy import deepcopy
from utils.settings_store import MAX_SETTINGS_CHARS, SettingsStore
from pet.fox_personality import FOX_PERSONALITIES


class MemoryBackend:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.writes = 0

    def read(self):
        return deepcopy(self.values)

    def write(self, values):
        self.values.update(deepcopy(values))
        self.writes += 1


class SettingsTests(unittest.TestCase):
    def test_corrupt_roster_survives_startup_autosave_and_unrelated_changes(self):
        invalid = ('["bad"]', 'null', '[]', '{}', '[null]', '[{"type":"../../etc"}]',
                   '[' * 4000 + '0' + ']' * 4000, ' ' * (MAX_SETTINGS_CHARS + 1))
        for raw in invalid:
            with self.subTest(raw_size=len(raw)):
                backend = MemoryBackend({'pet': 'panda', 'pets': raw})
                store = SettingsStore(backend)
                store.load()
                self.assertEqual(store.roster(), [{'type': 'panda'}])
                self.assertEqual(backend.writes, 0)
                store.save(pets=store.roster(), lang='en', menu_style='ring')
                self.assertEqual(backend.values['pets'], raw)
                self.assertEqual(backend.values['pet'], 'panda')
                self.assertEqual(backend.values['lang'], 'en')
                self.assertEqual(backend.values['menu_style'], 'ring')

    def test_explicit_recovery_replaces_only_after_authorization(self):
        backend = MemoryBackend({'pet': 'panda', 'pets': '{'})
        store = SettingsStore(backend)
        store.load()
        store.save(pets=[{'type': 'dog'}])
        self.assertEqual(backend.values['pets'], '{')
        store.save(replace_corrupt=True)
        self.assertEqual(json.loads(backend.values['pets']), [{'type': 'dog'}])
        restored = SettingsStore(backend)
        restored.load()
        self.assertEqual(restored.roster(), [{'type': 'dog'}])

    def test_no_hidden_count_limit_for_valid_roster(self):
        pets = [{'type': 'panda', 'name': str(index)} for index in range(1000)]
        backend = MemoryBackend({'pets': json.dumps(pets)})
        store = SettingsStore(backend)
        store.load()
        self.assertEqual(store.roster(), pets)

    def test_menu_style_defaults_and_rejects_invalid_values(self):
        for value in (None, '', 'radial', False, [], {}):
            store = SettingsStore(MemoryBackend({'pet': 'panda', 'menu_style': value}))
            store.load()
            self.assertEqual(store.menu_style, 'panel')
        store.save(menu_style='ring')
        store.save(menu_style='invalid')
        self.assertEqual(store.menu_style, 'ring')

    def test_menu_style_roundtrip_survives_roster_and_language_saves(self):
        backend = MemoryBackend()
        store = SettingsStore(backend)
        store.save(pets=[{'type': 'panda'}], menu_style='ring')
        store.save(lang='en')
        store.save(pets=[{'type': 'dog'}])
        restored = SettingsStore(backend)
        restored.load()
        self.assertEqual(restored.menu_style, 'ring')
        self.assertEqual(restored.roster(), [{'type': 'dog'}])
        self.assertEqual(restored.lang, 'en')

    def test_legacy_values_migrate_on_save(self):
        backend = MemoryBackend({"lang": "en", "pet": "panda"})
        store = SettingsStore(backend)
        store.load()
        self.assertEqual(store.roster(), [{"type": "panda"}])
        self.assertEqual(store.lang, "en")
        store.save()
        self.assertEqual(json.loads(backend.values["pets"]), [{"type": "panda"}])
        self.assertEqual(backend.values["pet"], "panda")

    def test_names_types_positions_roundtrip_and_removal(self):
        backend = MemoryBackend()
        store = SettingsStore(backend)
        records = [{"type": "fox", "name": "  Main  ", "position": [-500, -100], 'personality_id': 'active'},
                   {"type": "panda", "name": "Extra", "position": [50, 80]}]
        store.save(pets=records, lang="en")
        loaded = SettingsStore(backend)
        loaded.load()
        self.assertEqual(loaded.roster(), [dict(records[0], name="Main"), records[1]])
        loaded.save(pets=loaded.roster()[:1])
        again = SettingsStore(backend)
        again.load()
        self.assertEqual(len(again.roster()), 1)

    def test_corrupt_registry_values_are_rejected(self):
        for pets in ("{", "null", "[]", '{}', '[null]',
                     '[{"type":"../../etc"}]', '[{"type":false}]'):
            with self.subTest(pets=pets):
                store = SettingsStore(MemoryBackend({"lang": "xx", "pet": "invalid", "pets": pets}))
                store.load()
                self.assertEqual(store.lang, "ru")
                self.assertEqual(store.roster()[0]['type'], 'fox')
                self.assertIn(store.roster()[0]['personality_id'], FOX_PERSONALITIES)

    def test_invalid_optional_values_and_satellites(self):
        backend = MemoryBackend({"pets": json.dumps([
            {"type": "panda", "name": 8, "position": [True, 4]},
            {"type": "fox", "name": "  A  ", "position": [-20, 30]},
            {"type": "bogus"}, None])})
        store = SettingsStore(backend)
        store.load()
        self.assertEqual(store.roster(), [{"type": "panda"},
                         {"type": "fox", "name": "A", "position": [-20, 30],
                          'personality_id': store.roster()[1]['personality_id']}])
        self.assertIn(store.roster()[1]['personality_id'], FOX_PERSONALITIES)

    def test_language_update_preserves_entire_roster(self):
        backend = MemoryBackend()
        store = SettingsStore(backend)
        pets = [{"type": "fox", "name": str(n), 'personality_id': 'curious'} for n in range(40)]
        store.save(pets=pets)
        store.save(lang="en")
        store.load()
        self.assertEqual(store.roster(), pets)
        self.assertEqual(store.lang, "en")

    def test_roster_returns_copy(self):
        store = SettingsStore(MemoryBackend())
        copy = store.roster()
        copy[0]["type"] = "panda"
        self.assertEqual(store.roster()[0]["type"], "fox")

    def test_missing_registry_uses_defaults(self):
        class MissingBackend:
            def read(self):
                raise FileNotFoundError()

            def write(self, values):
                raise OSError("read only")
        store = SettingsStore(MissingBackend())
        store.load()
        store.save()
        self.assertEqual(store.roster()[0]['type'], 'fox')
        self.assertIn(store.roster()[0]['personality_id'], FOX_PERSONALITIES)


if __name__ == "__main__":
    unittest.main()
