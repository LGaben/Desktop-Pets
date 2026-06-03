# -*- coding: utf-8 -*-
from __future__ import annotations
import logging

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistence via Windows Registry  (HKCU\Software\DesktopPet)
# Works identically in dev mode and frozen exe — no files created.
# ---------------------------------------------------------------------------
_REGISTRY_PATH              = r"Software\DesktopPet"
_DEFAULTS: dict[str, str]   = {"lang": "ru", "pet": "fox"}

# In-memory cache — single source of truth; populated by load_settings()
_settings: dict[str, str]   = dict(_DEFAULTS)
_current_lang: str           = _DEFAULTS["lang"]


def load_settings() -> None:
    """Populate the in-memory cache from HKCU\\Software\\DesktopPet."""
    global _settings, _current_lang
    loaded: dict[str, str] = {}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH) as key:
            for name in _DEFAULTS:
                try:
                    val, _ = winreg.QueryValueEx(key, name)
                    loaded[name] = str(val)
                except FileNotFoundError:
                    pass
        _log.info("Settings loaded from registry: %s", loaded)
    except FileNotFoundError:
        _log.info("Registry key absent — first run, using defaults")
    except Exception as exc:
        _log.warning("Failed to load settings: %s", exc)
    _settings    = {**_DEFAULTS, **loaded}
    _current_lang = _settings["lang"]


def save_settings(updates: dict[str, str] | None = None) -> None:
    """Merge optional updates into cache then write all keys to registry."""
    if updates:
        _settings.update(updates)
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH) as key:
            for name, val in _settings.items():
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(val))
        _log.info("Settings saved to registry: %s", _settings)
    except Exception as exc:
        _log.warning("Failed to save settings: %s", exc)

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        # -- pet default names (used when creating a new pet) ---------------
        "name_fox":        "Рыжик",
        "name_panda":      "Панда",
        "name_cockatiel":  "Корелла",
        "name_dog":        "Бобик",
        "name_turtle":     "Черепаха",
        "name_totoro":     "Тоторо",
        "name_chicken":    "Курица",
        "name_clippy":     "Скрепка",
        "name_crab":       "Краб",
        "name_deno":       "Дено",
        "name_horse":      "Лошадь",
        "name_mod":        "Модик",
        "name_monkey":     "Мартышка",
        "name_morph":      "Морф",
        "name_rat":        "Крыска",
        "name_rocky":      "Роки",
        "name_rubber_duck":"Уточка",
        "name_skeleton":   "Скелет",
        "name_snail":      "Улитка",
        "name_snake":      "Змейка",
        "name_zappy":      "Заппи",
        # -- settings card display names ------------------------------------
        "card_fox":        "Лиса",
        "card_panda":      "Панда",
        "card_cockatiel":  "Корелла",
        "card_dog":        "Пёс",
        "card_turtle":     "Черепаха",
        "card_totoro":     "Тоторо",
        "card_chicken":    "Курица",
        "card_clippy":     "Скрепка",
        "card_crab":       "Краб",
        "card_deno":       "Дено",
        "card_horse":      "Лошадь",
        "card_mod":        "Мод",
        "card_monkey":     "Обезьяна",
        "card_morph":      "Морф",
        "card_rat":        "Крыса",
        "card_rocky":      "Роки",
        "card_rubber_duck":"Утка",
        "card_skeleton":   "Скелет",
        "card_snail":      "Улитка",
        "card_snake":      "Змея",
        "card_zappy":      "Заппи",
        # -- tray / context menu strings ------------------------------------
        "hide_pet":        "Скрыть питомца",
        "show_pet":        "Показать питомца",
        "hide_all":        "Скрыть всех",
        "show_all":        "Показать всех",
        "settings":        "⚙️ Настройки",
        "quit":            "❌ Выход",
        "throw_ball":      "\U0001f3be Кинуть мяч",
        "stop_follow":     "\U0001f50d Отключить слежение",
        "start_follow":    "\U0001f50d Следовать за мышкой",
        "wake_up":         "☀️ Разбудить",
        "sleep":           "\U0001f4a4 Спать",
        "hide_to_tray":    "\U0001f441 Скрыть в трей",
        "add_pet":         "➕ Добавить питомца",
        "remove_pet":      "\U0001f5d1 Убрать",
        "tray_hide_title": "Desktop Pet",
        "tray_hide_msg":   "Питомец свёрнут в трей.\nДвойной клик на иконке чтобы показать.",
        # -- settings window labels -----------------------------------------
        "sw_title":        "НАСТРОЙКИ",
        "sw_pet":          "ПИТОМЕЦ",
        "sw_name":         "ИМЯ",
        "sw_name_ph":      "Введите имя питомца…",
        "sw_language":     "ЯЗЫК",
        "sw_active_pets":  "НА ЭКРАНЕ",
        "sw_no_extra":     "— нет дополнительных питомцев —",
        "sw_add_pet":      "ДОБАВИТЬ",
        "sw_cancel":       "ОТМЕНА",
        "sw_apply":        "ПРИМЕНИТЬ",
        "sw_lang_ru":      "РУССКИЙ",
        "sw_lang_en":      "ENGLISH",
    },
    "en": {
        "name_fox":        "Rusty",
        "name_panda":      "Panda",
        "name_cockatiel":  "Cockatiel",
        "name_dog":        "Buddy",
        "name_turtle":     "Shelly",
        "name_totoro":     "Totoro",
        "name_chicken":    "Clucky",
        "name_clippy":     "Clippy",
        "name_crab":       "Crab",
        "name_deno":       "Deno",
        "name_horse":      "Horsey",
        "name_mod":        "Mod",
        "name_monkey":     "Monki",
        "name_morph":      "Morph",
        "name_rat":        "Ratty",
        "name_rocky":      "Rocky",
        "name_rubber_duck":"Ducky",
        "name_skeleton":   "Bones",
        "name_snail":      "Snaily",
        "name_snake":      "Snek",
        "name_zappy":      "Zappy",
        "card_fox":        "Fox",
        "card_panda":      "Panda",
        "card_cockatiel":  "Bird",
        "card_dog":        "Dog",
        "card_turtle":     "Turtle",
        "card_totoro":     "Totoro",
        "card_chicken":    "Chicken",
        "card_clippy":     "Clippy",
        "card_crab":       "Crab",
        "card_deno":       "Deno",
        "card_horse":      "Horse",
        "card_mod":        "Mod",
        "card_monkey":     "Monkey",
        "card_morph":      "Morph",
        "card_rat":        "Rat",
        "card_rocky":      "Rocky",
        "card_rubber_duck":"Duck",
        "card_skeleton":   "Skeleton",
        "card_snail":      "Snail",
        "card_snake":      "Snake",
        "card_zappy":      "Zappy",
        "hide_pet":        "Hide Pet",
        "show_pet":        "Show Pet",
        "hide_all":        "Hide All",
        "show_all":        "Show All",
        "settings":        "⚙️ Settings",
        "quit":            "❌ Quit",
        "throw_ball":      "\U0001f3be Throw Ball",
        "stop_follow":     "\U0001f50d Stop Following",
        "start_follow":    "\U0001f50d Follow Mouse",
        "wake_up":         "☀️ Wake Up",
        "sleep":           "\U0001f4a4 Sleep",
        "hide_to_tray":    "\U0001f441 Minimize to Tray",
        "add_pet":         "➕ Add Pet",
        "remove_pet":      "\U0001f5d1 Remove",
        "tray_hide_title": "Desktop Pet",
        "tray_hide_msg":   "Pet minimized to tray.\nDouble-click the icon to show.",
        "sw_title":        "SETTINGS",
        "sw_pet":          "PET",
        "sw_name":         "NAME",
        "sw_name_ph":      "Enter pet name…",
        "sw_language":     "LANGUAGE",
        "sw_active_pets":  "ON SCREEN",
        "sw_no_extra":     "— no extra pets —",
        "sw_add_pet":      "ADD",
        "sw_cancel":       "CANCEL",
        "sw_apply":        "APPLY",
        "sw_lang_ru":      "РУССКИЙ",
        "sw_lang_en":      "ENGLISH",
    },
}

def t(key: str) -> str:
    lang = _TRANSLATIONS.get(_current_lang, _TRANSLATIONS["ru"])
    return lang.get(key, _TRANSLATIONS["ru"].get(key, key))


def get_lang() -> str:
    return _current_lang


def set_lang(lang: str) -> None:
    """Update in-memory lang only. Prefer save_lang(lang) to also persist."""
    global _current_lang
    if lang in _TRANSLATIONS:
        _current_lang = lang
        _settings["lang"] = lang


def load_lang() -> None:
    """Backward-compat alias — delegates to load_settings()."""
    load_settings()


def save_lang(lang: str | None = None) -> None:
    """Persist language. Pass lang to set + persist in one call."""
    global _current_lang
    if lang is not None and lang in _TRANSLATIONS:
        _current_lang = lang
        _settings["lang"] = lang
    save_settings()


def get_pet() -> str:
    return _settings.get("pet", _DEFAULTS["pet"])


def save_pet(pet_type: str) -> None:
    save_settings({"pet": pet_type})
