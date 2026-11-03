# -*- coding: utf-8 -*-
from __future__ import annotations
import logging

from utils.settings_store import store
from pet.catalog import PET_TYPES

_log = logging.getLogger(__name__)


def load_settings() -> None:
    store.load()


def save_settings(updates=None) -> None:
    updates = updates or {}
    if updates.get("pet") in PET_TYPES:
        pets = store.roster()
        pets[0]["type"] = updates["pet"]
        store.save(pets=pets, lang=updates.get("lang"))
    else:
        store.save(lang=updates.get("lang"))


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
        "settings":        "Настройки",
        "quit":            "Выход",
        "throw_ball":      "Кинуть мяч",
        "stop_follow":     "Остановить слежение",
        "start_follow":    "Следовать постоянно",
        "wake_up":         "Разбудить",
        "sleep":           "Спать",
        "hide_to_tray":    "Скрыть в трей",
        "add_pet":         "Добавить питомца",
        "remove_pet":      "Убрать",
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
        "settings":        "Settings",
        "quit":            "Quit",
        "throw_ball":      "Throw Ball",
        "stop_follow":     "Stop following",
        "start_follow":    "Follow continuously",
        "wake_up":         "Wake Up",
        "sleep":           "Sleep",
        "hide_to_tray":    "Minimize to Tray",
        "add_pet":         "Add Pet",
        "remove_pet":      "Remove",
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

_TRANSLATIONS['ru'].update({
    'menu_style': 'Стиль меню', 'menu_panel': 'Панель', 'menu_ring': 'Кольцо',
    'pets_actions': 'Питомцы', 'app_actions': 'Приложение…',
    'pet_action': 'Погладить', 'ball_action': 'Мяч', 'more_actions': 'Ещё…',
    'ball_grab_hint': 'Возьмите мяч и отпустите в движении, чтобы бросить. Esc — отмена.',
    'personality_active': 'Активная · любит движение и игру',
    'personality_calm': 'Спокойная · чаще отдыхает',
    'personality_curious': 'Любопытная · интересуется курсором',
})
_TRANSLATIONS['en'].update({
    'menu_style': 'Menu style', 'menu_panel': 'Panel', 'menu_ring': 'Ring',
    'pets_actions': 'Pets', 'app_actions': 'Application…',
    'pet_action': 'Pet', 'ball_action': 'Ball', 'more_actions': 'More…',
    'ball_grab_hint': 'Grab the ball and release while moving to throw. Esc cancels.',
    'personality_active': 'Active · loves movement and play',
    'personality_calm': 'Calm · rests more often',
    'personality_curious': 'Curious · interested in the cursor',
})


def t(key: str) -> str:
    lang = _TRANSLATIONS.get(store.lang, _TRANSLATIONS["ru"])
    return lang.get(key, _TRANSLATIONS["ru"].get(key, key))


def get_lang() -> str:
    return store.lang


def set_lang(lang: str) -> None:
    """Update in-memory lang only. Prefer save_lang(lang) to also persist."""
    if lang in _TRANSLATIONS:
        store.lang = lang


def load_lang() -> None:
    """Backward-compat alias — delegates to load_settings()."""
    load_settings()


def save_lang(lang: str | None = None) -> None:
    """Persist language. Pass lang to set + persist in one call."""
    store.save(lang=lang)


def get_pet() -> str:
    return store.pets[0]["type"]


def save_pet(pet_type: str) -> None:
    save_settings({"pet": pet_type})
