"""Validated application settings, independent of translation and widgets."""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Protocol

from pet.catalog import PET_TYPES
from pet.fox_personality import FOX_PERSONALITIES, choose_personality


class SettingsBackend(Protocol):
    def read(self) -> dict:
        ...

    def write(self, values: dict[str, str]) -> None:
        """Update supplied keys, preserving keys absent from this patch."""
        ...


_log = logging.getLogger(__name__)
REGISTRY_PATH = r"Software\DesktopPet"
MENU_STYLES = ('panel', 'ring')
MAX_SETTINGS_CHARS = 4 * 1024 * 1024


class RegistryBackend:
    def read(self) -> dict:
        import winreg
        result = {}
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
            for name in ("lang", "pet", "pets", "menu_style"):
                try:
                    result[name] = winreg.QueryValueEx(key, name)[0]
                except FileNotFoundError:
                    pass
        return result

    def write(self, values: dict[str, str]) -> None:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH) as key:
            for name, value in values.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def validate_pet(value: object) -> dict | None:
    if not isinstance(value, dict) or value.get("type") not in PET_TYPES:
        return None
    result = {"type": value["type"]}
    if value['type'] == 'fox':
        result['personality_id'] = choose_personality(value.get('personality_id'))
    name = value.get("name")
    if isinstance(name, str) and name.strip():
        result["name"] = name.strip()[:80]
    position = value.get("position")
    if (isinstance(position, (list, tuple)) and len(position) == 2
            and all(type(n) is int and abs(n) <= 1000000 for n in position)):
        result["position"] = list(position)
    return result


class SettingsStore:
    def __init__(self, backend: SettingsBackend | None = None) -> None:
        self.backend = backend if backend is not None else RegistryBackend()
        self.lang = "ru"
        self.menu_style = 'panel'
        self.pets = [{"type": "fox"}]
        self._preserve_corrupt_roster = False

    def load(self) -> None:
        self._preserve_corrupt_roster = False
        try:
            values = self.backend.read()
        except (OSError, ImportError) as exc:
            _log.info("Settings unavailable; using defaults: %s", exc)
            values = {}
        self.lang = values.get("lang") if values.get("lang") in ("ru", "en") else "ru"
        self.menu_style = values.get('menu_style') if values.get('menu_style') in MENU_STYLES else 'panel'
        legacy = values.get("pet")
        self.pets = [{"type": legacy if legacy in PET_TYPES else "fox"}]
        migration_needed = 'pets' not in values
        try:
            encoded = values.get('pets', 'null')
            if not isinstance(encoded, str) or len(encoded) > MAX_SETTINGS_CHARS:
                raise ValueError('Invalid roster encoding or size')
            raw = json.loads(encoded)
            primary = validate_pet(raw[0]) if isinstance(raw, list) and raw else None
            if 'pets' in values and primary is None:
                raise ValueError('Invalid roster structure or primary pet')
            if isinstance(raw, list) and raw:
                if primary:
                    self.pets = [primary] + [pet for item in raw[1:]
                                             if (pet := validate_pet(item))]
                    migration_needed = any(
                        isinstance(item, dict) and item.get('type') == 'fox'
                        and (not isinstance(item.get('personality_id'), str)
                             or item['personality_id'] not in FOX_PERSONALITIES)
                        for item in raw)
                    if len(self.pets) != len(raw):
                        self._preserve_corrupt_roster = True
                        migration_needed = False
                        _log.warning('Invalid satellite records; keeping stored roster until explicit Settings Apply')
        except (TypeError, ValueError, RecursionError):
            self._preserve_corrupt_roster = 'pets' in values
            migration_needed = False
            _log.warning('Invalid roster settings; keeping stored data until explicit Settings Apply')
        migrated = [validate_pet(pet) for pet in self.pets]
        self.pets = migrated
        if migration_needed and any(pet['type'] == 'fox' for pet in self.pets):
            # Save a legacy/random assignment before the next load can reroll it.
            self.save()

    def save(self, pets: list[dict] | None = None, lang: str | None = None,
             menu_style: str | None = None, replace_corrupt: bool = False) -> None:
        if lang in ("ru", "en"):
            self.lang = lang
        if menu_style in MENU_STYLES:
            self.menu_style = menu_style
        if pets is not None:
            validated = [validate_pet(pet) for pet in pets]
            if validated and validated[0]:
                self.pets = [pet for pet in validated if pet]
        if replace_corrupt:
            self._preserve_corrupt_roster = False
        try:
            values = {'lang': self.lang, 'menu_style': self.menu_style}
            if not self._preserve_corrupt_roster:
                values.update(pet=self.pets[0]['type'], pets=json.dumps(self.pets, ensure_ascii=False))
            self.backend.write(values)
        except (OSError, ImportError) as exc:
            _log.warning("Failed to save settings: %s", exc)

    def roster(self) -> list[dict]:
        return deepcopy(self.pets)


store = SettingsStore()
