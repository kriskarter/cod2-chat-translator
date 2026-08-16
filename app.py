from __future__ import annotations

import argparse
import ctypes
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from collections import OrderedDict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from update_client import UpdateInfo, check_github_release, load_release_config

if os.name == "nt":
    from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception:  # pragma: no cover
    tk = None
    filedialog = messagebox = ttk = None

APP_NAME = "CoD2 Chat Translator"
APP_VERSION = "1.11.1"
PROJECT_AUTHOR = "kriskarter"
PROJECT_PROFILE_URL = "https://github.com/kriskarter"
CONFIG_FILE = "config.json"
SETTINGS_DIR_NAME = "CoD2ChatTranslator"
COD_COLOR_RE = re.compile(r"\^[0-9]")
CHAT_LINE_RE = re.compile(
    r"^(?P<nickname>.+?)\^7(?P<role>\s+\(admin\))?:\s*(?:\^7)?(?P<text>.+)$"
)
SENSITIVE_LINE_TOKENS = (
    "ui_pwlogin",
    "rcon_password",
    "password ",
    "logininfo.cfg",
)

TARGET_LANGUAGES = OrderedDict([
    ("Русский", "ru"),
    ("Українська", "uk"),
    ("English", "en"),
    ("Deutsch", "de"),
    ("Polski", "pl"),
    ("Español", "es"),
    ("Français", "fr"),
    ("Italiano", "it"),
    ("Português", "pt"),
    ("Čeština", "cs"),
    ("Slovenčina", "sk"),
    ("Română", "ro"),
    ("Magyar", "hu"),
    ("Türkçe", "tr"),
    ("Nederlands", "nl"),
    ("Svenska", "sv"),
    ("Norsk", "no"),
    ("Dansk", "da"),
    ("Suomi", "fi"),
    ("Ελληνικά", "el"),
    ("Български", "bg"),
    ("Српски", "sr"),
    ("Hrvatski", "hr"),
    ("Slovenščina", "sl"),
    ("Bosanski", "bs"),
    ("Македонски", "mk"),
    ("Беларуская", "be"),
    ("Lietuvių", "lt"),
    ("Latviešu", "lv"),
    ("Eesti", "et"),
    ("العربية", "ar"),
    ("עברית", "iw"),
    ("हिन्दी", "hi"),
    ("Bahasa Indonesia", "id"),
    ("Tiếng Việt", "vi"),
    ("ไทย", "th"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("简体中文", "zh-CN"),
    ("繁體中文", "zh-TW"),
])

SLANG_STYLES = OrderedDict([
    ("Понятный", "clear"),
    ("Живой", "live"),
    ("Без цензуры", "raw"),
])

DEFAULT_CONFIG = {
    "ui_language": "ru",
    "log_path": "",
    "target_language": "ru",
    "show_original": False,
    "hide_same_language": True,
    "gaming_slang": True,
    "slang_style": "live",
    "deduplicate_messages": True,
    "duplicate_window_seconds": 4,
    "overlay": {
        "x": 8,
        "y": 360,
        "width": 500,
        "height": 150,
        "max_messages": 2,
        "font_size": 10,
        "background_opacity": 0.15,
        "background_only_with_messages": True,
        "message_ttl_seconds": 10,
        "auto_height": True,
        "compact_background": True,
        "fade_enabled": True,
        "fade_ms": 220,
    },
}

UI_STRINGS = {
    "ru": {
        "subtitle": "Автоперевод чата из console_mp.log + настраиваемый оверлей поверх CoD2.",
        "log": "Лог CoD2:", "browse": "Выбрать…", "translate_to": "Переводить на:", "other": "Другой…",
        "show_original": "показывать оригинал", "hide_same": "не дублировать выбранный язык", "smart_chat": "Умный чат:",
        "gaming_slang": "игровой сленг (gg/wp/ns/afk/hs/tk…)", "style": "Стиль:", "dedupe": "убирать повторы (4 с)",
        "hotkey": "F8 — скрыть/показать", "enabled": "Переводчик включён", "test": "Тест оверлея", "clear": "Очистить",
        "configure_overlay": "Настроить оверлей", "lock_overlay": "Зафиксировать оверлей", "cod2_top": "CoD2 → поверх",
        "overlay_view": "Вид оверлея", "font_size": "Размер текста", "background": "Фон",
        "bg_only": "фон только во время сообщений", "compact_bg": "подложка по размеру текста", "show_for": "Показывать",
        "fade": "плавное появление/исчезновение", "messages": "Сообщений", "text_only": "Только текст", "minimal": "Минимальный",
        "readable": "Читаемый", "standard_place": "Стандартное место", "wheel": "Ctrl+колесо = размер",
        "ready": "Готов", "last": "Последнее сообщение: —", "privacy": "Важно: console_mp.log может содержать служебные данные и пароли сервера. Не публикуй лог целиком. В сервис перевода отправляется только текст уже отфильтрованного сообщения чата.",
        "interface": "Интерфейс:", "check_updates": "Проверить обновления", "updates": "Обновления", "update_checking": "Проверяю обновления…",
        "update_none": "Установлена последняя версия.", "update_unconfigured": "Канал обновлений ещё не настроен.",
        "update_available_title": "Доступно обновление", "update_available": "Доступна версия {version}.\n\n{notes}\n\nУстановить обновление сейчас?",
        "update_error": "Не удалось проверить обновления: {error}", "choose_log": "Выбери console_mp.log", "all_files": "Все файлы",
        "about": "О программе", "developer": "Разработчик", "github": "GitHub", "star_project": "⭐ Поддержать проект",
        "repo_pending": "Репозиторий проекта появится после публикации публичного релиза.",
        "made_for": "Сделано для сообщества Call of Duty 2.", "close": "Закрыть",
        "custom_language": "Другой язык", "custom_prompt": "Введи код языка Google Translate, например: cs, ja, ro, ko, ar",
        "custom_invalid": "Нужен короткий код языка, например ja, cs, ro или zh-CN.",
        "style_clear": "Понятный", "style_live": "Живой", "style_raw": "Без цензуры",
    },
    "en": {
        "subtitle": "Real-time translation from console_mp.log + a configurable overlay over CoD2.",
        "log": "CoD2 log:", "browse": "Browse…", "translate_to": "Translate to:", "other": "Other…",
        "show_original": "show original", "hide_same": "hide messages already in target language", "smart_chat": "Smart chat:",
        "gaming_slang": "gaming slang (gg/wp/ns/afk/hs/tk…)", "style": "Style:", "dedupe": "remove duplicates (4 s)",
        "hotkey": "F8 — hide/show", "enabled": "Translator enabled", "test": "Test overlay", "clear": "Clear",
        "configure_overlay": "Configure overlay", "lock_overlay": "Lock overlay", "cod2_top": "CoD2 → overlay",
        "overlay_view": "Overlay appearance", "font_size": "Text size", "background": "Background",
        "bg_only": "background only with messages", "compact_bg": "fit background to text", "show_for": "Show for",
        "fade": "fade in/out", "messages": "Messages", "text_only": "Text only", "minimal": "Minimal",
        "readable": "Readable", "standard_place": "Default position", "wheel": "Ctrl+wheel = font size",
        "ready": "Ready", "last": "Last message: —", "privacy": "Important: console_mp.log may contain service data and server passwords. Do not publish the whole log. Only the filtered chat message text is sent to the translation service.",
        "interface": "Interface:", "check_updates": "Check for updates", "updates": "Updates", "update_checking": "Checking for updates…",
        "update_none": "You have the latest version.", "update_unconfigured": "The update channel is not configured yet.",
        "update_available_title": "Update available", "update_available": "Version {version} is available.\n\n{notes}\n\nInstall the update now?",
        "update_error": "Could not check for updates: {error}", "choose_log": "Select console_mp.log", "all_files": "All files",
        "about": "About", "developer": "Developer", "github": "GitHub", "star_project": "⭐ Star the project",
        "repo_pending": "The project repository will be available after the public release is published.",
        "made_for": "Made for the Call of Duty 2 community.", "close": "Close",
        "custom_language": "Other language", "custom_prompt": "Enter a Google Translate language code, for example: cs, ja, ro, ko, ar",
        "custom_invalid": "Enter a short language code such as ja, cs, ro or zh-CN.",
        "style_clear": "Clear", "style_live": "Natural", "style_raw": "Uncensored",
    },
}



def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", app_dir()))
    return base / relative


def settings_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    path = base / SETTINGS_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return settings_dir() / CONFIG_FILE


def legacy_config_path() -> Path:
    return app_dir() / CONFIG_FILE


def installer_language_hint() -> str:
    hint = settings_dir() / "ui_language.txt"
    try:
        value = hint.read_text(encoding="utf-8").strip().lower()
        if value in {"ru", "en"}:
            return value
    except Exception:
        pass
    return "ru"


def migrate_legacy_config_if_needed() -> None:
    target = config_path()
    if target.exists():
        return
    old = legacy_config_path()
    if old.exists() and old.resolve() != target.resolve():
        try:
            shutil.copy2(old, target)
            backup = old.with_name("config.backup.json")
            if backup.exists():
                shutil.copy2(backup, target.with_name("config.backup.json"))
            return
        except Exception:
            pass
    # First installed launch: let the installer language become the UI language.
    try:
        lang = installer_language_hint()
        target.write_text(json.dumps({"ui_language": lang, "target_language": ("en" if lang == "en" else "ru")}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def deep_merge(base: dict, custom: dict) -> dict:
    result = dict(base)
    for key, value in custom.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    migrate_legacy_config_if_needed()
    path = config_path()
    if not path.exists():
        return deep_merge(DEFAULT_CONFIG, {})
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("config root must be an object")
        return deep_merge(DEFAULT_CONFIG, raw)
    except Exception:
        return deep_merge(DEFAULT_CONFIG, {})


def save_config(config: dict) -> None:
    """Atomically save settings and keep one automatic backup.

    Slider changes are saved immediately.  Atomic replace avoids a half-written
    config if Windows or the app closes at an unlucky moment; the previous file
    is also copied to ``config.backup.json`` for easy recovery.
    """
    path = config_path()
    backup = path.with_name("config.backup.json")
    temp = path.with_name("config.tmp.json")
    try:
        if path.exists():
            shutil.copy2(path, backup)
    except Exception:
        pass
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)



def _steam_library_paths() -> list[Path]:
    paths: list[Path] = []
    if os.name == "nt":
        try:
            import winreg
            for root, key, name in [
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            ]:
                try:
                    with winreg.OpenKey(root, key) as h:
                        value, _ = winreg.QueryValueEx(h, name)
                        if value:
                            paths.append(Path(value))
                except OSError:
                    pass
        except Exception:
            pass
        for env_name in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(env_name)
            if base:
                paths.append(Path(base) / "Steam")
    # Parse Steam libraryfolders.vdf using a forgiving quoted-path scan.
    expanded: list[Path] = []
    for steam in paths:
        if steam not in expanded:
            expanded.append(steam)
        vdf = steam / "steamapps" / "libraryfolders.vdf"
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'"path"\s+"([^"]+)"', text, flags=re.I):
                lib = Path(match.group(1).replace("\\\\", "\\"))
                if lib not in expanded:
                    expanded.append(lib)
        except Exception:
            pass
    return expanded


def discover_cod2_logs() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    roots = _steam_library_paths()
    # Include the portable/source folder as a compatibility fallback.
    roots.extend([app_dir(), Path.cwd()])
    for root in roots:
        possible_game_dirs = [
            root / "steamapps" / "common" / "Call of Duty 2",
            root / "Call of Duty 2",
            root,
        ]
        for game in possible_game_dirs:
            try:
                if not game.exists() or not game.is_dir():
                    continue
                for log in game.glob("*/console_mp.log"):
                    key = str(log.resolve()).lower()
                    if key not in seen:
                        seen.add(key); candidates.append(log.resolve())
                direct = game / "console_mp.log"
                if direct.exists():
                    key = str(direct.resolve()).lower()
                    if key not in seen:
                        seen.add(key); candidates.append(direct.resolve())
            except Exception:
                pass
    candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return candidates


def release_config_path() -> Path:
    installed = app_dir() / "release_config.json"
    if installed.exists():
        return installed
    return resource_path("release_config.json")

def strip_cod_colors(text: str) -> str:
    return COD_COLOR_RE.sub("", text).strip()


@dataclass(frozen=True)
class ChatMessage:
    nickname: str
    text: str
    raw: str = ""


def parse_chat_line(line: str) -> Optional[ChatMessage]:
    """Parse only real CoD2 chat lines.

    Map changes can dump thousands of dvars, errors and file paths into the same
    log.  Chat has a much more specific color-coded shape, for example::

        Player^7: ^7hello
        Player^7 (admin): ^7server message

    Keeping this parser strict prevents map-load noise (and sensitive dvars)
    from ever reaching the translation service.
    """
    line = line.rstrip("\r\n")
    lowered = line.lower()
    if any(token in lowered for token in SENSITIVE_LINE_TOKENS):
        return None

    match = CHAT_LINE_RE.match(line)
    if not match:
        return None

    nickname = strip_cod_colors(match.group("nickname"))
    role = (match.group("role") or "").strip()
    text = strip_cod_colors(match.group("text"))
    if role:
        nickname = f"{nickname} {role}"

    if not nickname or not text:
        return None
    return ChatMessage(nickname=nickname, text=text, raw=line)


def read_log_messages(path: Path) -> list[ChatMessage]:
    """Read a complete CoD2 log using Windows-1251, as observed in the sample."""
    data = path.read_bytes()
    text = data.decode("cp1251", errors="replace")
    messages: list[ChatMessage] = []
    for line in text.splitlines():
        msg = parse_chat_line(line)
        if msg:
            messages.append(msg)
    return messages


RUSSIAN_HINT_WORDS = {
    "а", "без", "блин", "больше", "будет", "бы", "в", "вам", "вас", "все", "всё", "вот",
    "враг", "где", "да", "давай", "дима", "для", "его", "если", "есть", "здесь", "и", "иди",
    "из", "или", "как", "когда", "кто", "куда", "меня", "мне", "можно", "мы", "на", "не", "нет",
    "но", "ну", "он", "они", "по", "под", "пока", "привет", "прикрой", "с", "слева", "справа",
    "там", "тебя", "тут", "ты", "у", "уже", "что", "это", "я", "убил", "уничтожен",
}
CYRILLIC_RE = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґЎўЈјЉљЊњЋћЂђЏџЃѓЌќЅѕ]")
WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґЎўЈјЉљЊњЋћЂђЏџЃѓЌќЅѕ]+")


def normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def normalize_slang_key(text: str) -> str:
    key = normalize_for_compare(text)
    return key.strip(" .,!?:;…")


# Short gaming messages are extremely context-dependent.  Online translators
# often misread abbreviations (the classic example is ``gg``), so V1.7 expands
# common FPS/chat slang before translation.  V1.7 expands the dictionary with
# common CoD2/FPS phrases and keeps exact short messages deterministic.  Slang
# embedded in a longer sentence is expanded in-place before normal translation.
EN_GAMING_SLANG_EXPANSIONS = {
    "gg wp": "good game, well played",
    "ggwp": "good game, well played",
    "gl hf": "good luck, have fun",
    "glhf": "good luck, have fun",
    "good luck have fun": "good luck, have fun",
    "cover me": "cover me",
    "low hp": "low health",
    "1 hp": "almost no health",
    "1hp": "almost no health",
    "no scope": "without using the scope",
    "noscope": "without using the scope",
    "spawn kill": "kill immediately after spawn",
    "spawnkill": "kill immediately after spawn",
    "spawn camp": "camp near the enemy spawn",
    "spawncamp": "camp near the enemy spawn",
    "spawn rape": "repeatedly kill players at their spawn",
    "spawnrape": "repeatedly kill players at their spawn",
    "rush b": "rush attack toward B",
    "rush a": "rush attack toward A",
    "go b": "go to B",
    "go a": "go to A",
    "go mid": "go through the middle",
    "behind you": "enemy behind you",
    "one shot": "enemy needs one more hit",
    "one hit": "enemy needs one more hit",
    "nice one": "nice play",
    "nice kill": "nice kill",
    "good shot": "good shot",
    "packet loss": "network packet loss",
    "fps drop": "frame rate drop",
    "low fps": "low frame rate",
    "vote kick": "vote to kick a player",
    "votekick": "vote to kick a player",
    "next map": "next map",
    "gg": "good game",
    "ggs": "good games",
    "wp": "well played",
    "gj": "good job",
    "bg": "bad game",
    "gl": "good luck",
    "hf": "have fun",
    "ns": "nice shot",
    "nt": "nice try",
    "afk": "away from keyboard",
    "brb": "be right back",
    "bbl": "be back later",
    "gtg": "got to go",
    "g2g": "got to go",
    "cya": "see you",
    "cu": "see you",
    "ty": "thank you",
    "tyvm": "thank you very much",
    "thx": "thank you",
    "tnx": "thank you",
    "np": "no problem",
    "nvm": "never mind",
    "pls": "please",
    "plz": "please",
    "sry": "sorry",
    "soz": "sorry",
    "mb": "my bad",
    "idk": "I do not know",
    "idc": "I do not care",
    "imo": "in my opinion",
    "imho": "in my humble opinion",
    "wdym": "what do you mean",
    "omw": "on my way",
    "rn": "right now",
    "rdy": "ready",
    "omg": "oh my god",
    "lol": "laughing",
    "rofl": "laughing a lot",
    "lmao": "laughing a lot",
    "wtf": "what the fuck",
    "wth": "what the heck",
    "ffs": "for fuck's sake",
    "stfu": "shut the fuck up",
    "fu": "fuck you",
    "fk": "fuck",
    "fck": "fuck",
    "fuck": "fuck",
    "fucking": "fucking",
    "shit": "shit",
    "damn": "damn",
    "bitch": "bitch",
    "asshole": "asshole",
    "mf": "motherfucker",
    "motherfucker": "motherfucker",
    "bro": "bro",
    "dude": "dude",
    "mate": "mate",
    "ez": "easy",
    "noob": "new or inexperienced player",
    "n00b": "new or inexperienced player",
    "tk": "team kill",
    "teamkill": "team kill",
    "ff": "friendly fire",
    "hs": "headshot",
    "headshot": "headshot",
    "hp": "health",
    "nade": "grenade",
    "frag": "frag grenade",
    "smoke": "smoke grenade",
    "flash": "flash grenade",
    "ammo": "ammunition",
    "reload": "reload",
    "reloading": "reloading",
    "rush": "rush attack",
    "push": "push forward",
    "flank": "attack from the flank",
    "mid": "middle",
    # CoD/FPS camping needs context: literal machine translation often turns
    # "camp" into a tourist camp. Longer phrases are matched first.
    "stop camping": "stop staying in one position waiting for enemies",
    "stop camp": "stop staying in one position waiting for enemies",
    "dont camp": "do not stay in one position waiting for enemies",
    "don't camp": "do not stay in one position waiting for enemies",
    "do not camp": "do not stay in one position waiting for enemies",
    "no camping": "do not stay in one position waiting for enemies",
    "camping": "staying in one position waiting for enemies",
    "campers": "players staying in one position waiting for enemies",
    "camped": "stayed in one position waiting for enemies",
    "camp": "stay in one position waiting for enemies",
    "camper": "player staying in one position waiting for enemies",
    "spawn": "spawn point",
    "respawn": "respawn",
    "scope": "scope",
    "spec": "spectator mode",
    "spect": "spectator mode",
    "spectator": "spectator",
    "bash": "melee hit",
    "bashed": "hit with a melee attack",
    "melee": "melee attack",
    "ping": "network ping",
    "lag": "network lag",
    "fps": "frames per second",
    "kick": "kick from the server",
    "ban": "ban from the server",
    "cheater": "cheater",
    "hacker": "cheater",
    "aimbot": "aimbot cheat",
    "wallhack": "wallhack cheat",
    "wh": "wallhack cheat",
    "esp": "ESP cheat",
    "aim": "aiming",
    "arty": "artillery",
    "artillery": "artillery strike",
    "airstrike": "air strike",
    "ks": "kill streak",
    "killstreak": "kill streak",
    "clutch": "win a difficult situation alone",
    "carry": "carry the team",
    "owned": "completely outplayed",
    "pwned": "completely outplayed",
    "rekt": "completely outplayed",
    "enemy": "enemy",
    "enemies": "enemies",
    "left": "left side",
    "right": "right side",
    "base": "base",
    "flag": "flag",
    "objective": "objective",
    "tdm": "team deathmatch",
    "dm": "deathmatch",
    "ctf": "capture the flag",
    "sd": "search and destroy",
    "hq": "headquarters",
}

# Expand Russian gamer shorthand into normal Russian before translating to a
# non-Russian target.  Keeping the expansion in the source language gives the
# automatic translator better context inside mixed/longer sentences.
RU_GAMING_SLANG_EXPANSIONS = {
    "гг": "хорошая игра",
    "вп": "хорошо сыграно",
    "нс": "хороший выстрел",
    "нт": "хорошая попытка",
    "спс": "спасибо",
    "сяб": "спасибо",
    "пж": "пожалуйста",
    "плз": "пожалуйста",
    "сорян": "извини",
    "сори": "извини",
    "прив": "привет",
    "афк": "отошёл от компьютера",
    "брб": "скоро вернусь",
    "хз": "не знаю",
    "имхо": "по моему мнению",
    "норм": "нормально",
    "изи": "легко",
    "нуб": "неопытный игрок",
    "тк": "убийство союзника",
    "тимкилл": "убийство союзника",
    "френдлифаер": "огонь по своим",
    "хед": "выстрел в голову",
    "хедшот": "выстрел в голову",
    "хп": "здоровье",
    "грен": "граната",
    "смок": "дымовая граната",
    "флеш": "светошумовая граната",
    "раш": "быстрая атака",
    "рашить": "быстро атаковать",
    "пуш": "наступление",
    "фланг": "атака с фланга",
    "мид": "центр",
    "кемпер": "игрок, сидящий в засаде",
    "респ": "точка появления",
    "респавн": "повторное появление",
    "спек": "режим наблюдателя",
    "лаги": "задержки сети",
    "арта": "артиллерия",
    "авиа": "авиаудар",
    "серия": "серия убийств",
    "слева": "слева",
    "справа": "справа",
    "сзади": "враг сзади",
    "база": "база",
    "флаг": "флаг",
}

RU_GAMING_DIRECT = {
    "gg": "хорошая игра",
    "ggs": "хорошие игры",
    "wp": "хорошо сыграно",
    "gg wp": "хорошая игра, хорошо сыграно",
    "ggwp": "хорошая игра, хорошо сыграно",
    "gj": "молодец",
    "bg": "плохая игра",
    "gl": "удачи",
    "hf": "приятной игры",
    "gl hf": "удачи, приятной игры",
    "glhf": "удачи, приятной игры",
    "ns": "хороший выстрел",
    "nt": "хорошая попытка",
    "afk": "отошёл от компьютера",
    "brb": "скоро вернусь",
    "bbl": "вернусь позже",
    "gtg": "мне пора",
    "g2g": "мне пора",
    "cya": "увидимся",
    "cu": "увидимся",
    "ty": "спасибо",
    "tyvm": "большое спасибо",
    "thx": "спасибо",
    "tnx": "спасибо",
    "np": "без проблем",
    "nvm": "неважно",
    "pls": "пожалуйста",
    "plz": "пожалуйста",
    "sry": "извини",
    "soz": "извини",
    "mb": "моя ошибка",
    "idk": "не знаю",
    "idc": "мне всё равно",
    "imo": "по-моему",
    "imho": "по моему мнению",
    "wdym": "что ты имеешь в виду",
    "omw": "уже иду",
    "rn": "прямо сейчас",
    "rdy": "готов",
    "omg": "ого",
    "lol": "смешно",
    "rofl": "очень смешно",
    "lmao": "очень смешно",
    "wtf": "что за фигня",
    "wth": "что за фигня",
    "ffs": "да ё-моё",
    "stfu": "замолчи",
    "fu": "иди нафиг",
    "fk": "ругательство",
    "fck": "ругательство",
    "fuck": "ругательство",
    "fucking": "чёртов",
    "shit": "дерьмо",
    "damn": "чёрт",
    "bitch": "зараза",
    "asshole": "придурок",
    "mf": "ублюдок",
    "motherfucker": "ублюдок",
    "bro": "братан",
    "dude": "чувак",
    "mate": "бро",
    "ez": "легко",
    "noob": "неопытный игрок",
    "n00b": "неопытный игрок",
    "tk": "убийство союзника",
    "teamkill": "убийство союзника",
    "ff": "огонь по своим",
    "hs": "выстрел в голову",
    "headshot": "выстрел в голову",
    "hp": "здоровье",
    "low hp": "мало здоровья",
    "1 hp": "почти нет здоровья",
    "1hp": "почти нет здоровья",
    "nade": "граната",
    "frag": "осколочная граната",
    "smoke": "дымовая граната",
    "flash": "светошумовая граната",
    "ammo": "патроны",
    "reload": "перезаряжаюсь",
    "reloading": "перезаряжаюсь",
    "rush": "быстрая атака",
    "push": "наступаем",
    "flank": "заходим с фланга",
    "mid": "центр",
    "stop camping": "перестань сидеть в засаде",
    "stop camp": "перестань сидеть в засаде",
    "dont camp": "не сиди в засаде",
    "don't camp": "не сиди в засаде",
    "do not camp": "не сиди в засаде",
    "no camping": "не сиди в засаде",
    "camping": "сидеть в засаде",
    "campers": "кемперы",
    "camped": "сидел в засаде",
    "camp": "сидеть в засаде",
    "camper": "кемпер",
    "spawn": "точка появления",
    "respawn": "повторное появление",
    "spawn kill": "убийство сразу после появления",
    "spawnkill": "убийство сразу после появления",
    "scope": "прицел",
    "no scope": "без прицела",
    "noscope": "без прицела",
    "spec": "режим наблюдателя",
    "spect": "режим наблюдателя",
    "spectator": "наблюдатель",
    "bash": "удар прикладом",
    "bashed": "ударил в ближнем бою",
    "melee": "ближний бой",
    "cover me": "прикрой меня",
    "ping": "пинг",
    "lag": "лаги",
    "fps": "кадров в секунду",
    "kick": "выгнать с сервера",
    "ban": "заблокировать на сервере",
    "cheater": "читер",
    "hacker": "читер",
    "aimbot": "чит на автоприцеливание",
    "wallhack": "чит для видения сквозь стены",
    "wh": "чит для видения сквозь стены",
    "esp": "чит ESP",
    "arty": "артиллерия",
    "artillery": "артиллерийский удар",
    "airstrike": "авиаудар",
    "ks": "серия убийств",
    "killstreak": "серия убийств",
    "spawn camp": "засада у точки появления",
    "spawncamp": "засада у точки появления",
    "spawn rape": "постоянные убийства на точке появления",
    "spawnrape": "постоянные убийства на точке появления",
    "rush b": "быстрая атака на B",
    "rush a": "быстрая атака на A",
    "go b": "идём на B",
    "go a": "идём на A",
    "go mid": "идём через центр",
    "behind you": "враг сзади",
    "one shot": "врагу остался один выстрел",
    "one hit": "врагу остался один удар",
    "nice one": "красиво сыграно",
    "nice kill": "хорошее убийство",
    "good shot": "хороший выстрел",
    "packet loss": "потеря сетевых пакетов",
    "fps drop": "просадка FPS",
    "low fps": "низкий FPS",
    "vote kick": "голосование за кик",
    "votekick": "голосование за кик",
    "next map": "следующая карта",
    "clutch": "вытащил сложную ситуацию в одиночку",
    "carry": "тащить команду",
    "owned": "полностью переигран",
    "pwned": "полностью переигран",
    "rekt": "полностью переигран",
    "enemy": "враг",
    "enemies": "враги",
    "left": "слева",
    "right": "справа",
    "base": "база",
    "flag": "флаг",
    "objective": "цель",
    "tdm": "командный бой",
    "dm": "каждый сам за себя",
    "ctf": "захват флага",
    "sd": "поиск и уничтожение",
    "hq": "штаб",
}

# Optional Russian tone overlays.  They never invent profanity: the raw mode
# is only stronger when the source slang itself is profane.  "live" keeps the
# short, joking style common on adult CoD2 servers.
RU_GAMING_LIVE_DIRECT = {
    "wtf": "какого хрена",
    "wth": "какого хрена",
    "ffs": "да ё-моё",
    "stfu": "заткнись",
    "fu": "иди нафиг",
    "ez": "изи",
    "noob": "нуб",
    "n00b": "нуб",
    "bro": "братан",
    "dude": "чувак",
    "mate": "бро",
    "stop camping": "хватит кемперить",
    "stop camp": "хватит кемперить",
    "dont camp": "не кемпери",
    "don't camp": "не кемпери",
    "do not camp": "не кемпери",
    "no camping": "не кемпери",
    "camping": "кемперит",
    "campers": "кемперы",
    "camped": "кемперил",
    "camper": "кемпер",
    "camp": "кемперить",
    "owned": "размотал",
    "pwned": "размотал",
    "rekt": "разнесли",
    "clutch": "затащил",
    "carry": "тащит команду",
    "nice one": "красавчик",
    "nice kill": "красиво снял",
    "good shot": "красиво попал",
    "lol": "ахаха",
    "rofl": "ору",
    "lmao": "ору",
}

RU_GAMING_RAW_DIRECT = {
    **RU_GAMING_LIVE_DIRECT,
    "wtf": "что за хуйня",
    "ffs": "да блядь",
    "stfu": "заткнись нахуй",
    "fu": "пошёл нахуй",
    "fuck you": "пошёл нахуй",
    "fuck": "блядь",
    "fucking": "ёбаный",
    "shit": "дерьмо",
    "bitch": "сука",
    "asshole": "мудак",
    "mf": "ублюдок",
    "motherfucker": "ублюдок",
    "stop camping": "хватит крысить",
    "stop camp": "хватит крысить",
    "dont camp": "не крысь",
    "don't camp": "не крысь",
    "do not camp": "не крысь",
    "no camping": "не крысь",
    "camping": "крысит",
    "campers": "крысы",
    "camped": "крысил",
    "camper": "крыса",
    "camp": "крысить",
}

EN_FROM_RU_GAMING_DIRECT = {
    "гг": "good game",
    "вп": "well played",
    "нс": "nice shot",
    "нт": "nice try",
    "спс": "thanks",
    "сяб": "thanks",
    "пж": "please",
    "плз": "please",
    "сорян": "sorry",
    "сори": "sorry",
    "прив": "hi",
    "афк": "away from keyboard",
    "брб": "be right back",
    "хз": "I do not know",
    "имхо": "in my opinion",
    "норм": "fine",
    "изи": "easy",
    "нуб": "inexperienced player",
    "тк": "team kill",
    "тимкилл": "team kill",
    "френдлифаер": "friendly fire",
    "хед": "headshot",
    "хедшот": "headshot",
    "хп": "health",
    "грен": "grenade",
    "смок": "smoke grenade",
    "флеш": "flash grenade",
    "раш": "rush attack",
    "рашить": "rush attack",
    "пуш": "push forward",
    "фланг": "flank",
    "мид": "middle",
    "кемпер": "camper",
    "респ": "spawn point",
    "респавн": "respawn",
    "спек": "spectator mode",
    "лаги": "network lag",
    "арта": "artillery",
    "авиа": "air strike",
    "серия": "kill streak",
    "сзади": "enemy behind you",
    "база": "base",
    "флаг": "flag",
}

def _replace_slang_in_text(text: str, mapping: dict[str, str]) -> str:
    """Replace slang in one pass so replacement text is never expanded again.

    Longer phrases are matched first (``rush b`` before ``rush``), and ``\\w``
    boundaries keep abbreviations from being changed inside normal words.
    """
    if not mapping:
        return text
    keys = sorted(mapping, key=len, reverse=True)
    alternatives = "|".join(re.escape(key) for key in keys)
    pattern = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)
    folded = {key.casefold(): value for key, value in mapping.items()}
    return pattern.sub(lambda match: folded.get(match.group(0).casefold(), match.group(0)), text)

def _append_terminal_punctuation(original: str, result: str) -> str:
    match = re.search(r"([!?…]+)$", original.strip())
    if match and not result.rstrip().endswith(match.group(1)):
        return result.rstrip() + match.group(1)
    return result

def _ru_contextual_gaming_phrase(text: str, style: str) -> Optional[str]:
    """Natural RU rendering for short malformed gamer-English phrases.

    Players often type things like ``stop camp idiot`` rather than grammatical
    English.  Translators can read ``camp`` as a tourist camp, so handle the
    most common CoD/FPS camping commands before generic translation.
    """
    stripped = text.strip()
    punctuation = ""
    m_punct = re.search(r"([!?…]+)$", stripped)
    if m_punct:
        punctuation = m_punct.group(1)
        stripped = stripped[:-len(punctuation)].rstrip()

    m = re.fullmatch(
        r"(?:stop|quit)\s+camp(?:ing)?(?:\s*,?\s*(idiot|noob|n00b|bro|dude|mate))?",
        stripped,
        flags=re.IGNORECASE,
    )
    if m:
        base = {
            "clear": "перестань сидеть в засаде",
            "live": "хватит кемперить",
            "raw": "хватит крысить",
        }.get(style, "хватит кемперить")
        tails = {
            "idiot": "идиот",
            "noob": "нуб",
            "n00b": "нуб",
            "bro": "братан",
            "dude": "чувак",
            "mate": "бро",
        }
        tail = tails.get((m.group(1) or "").casefold())
        return base + (f", {tail}" if tail else "") + punctuation

    m = re.fullmatch(
        r"(?:dont|don't|do\s+not)\s+camp(?:ing)?(?:\s*,?\s*(idiot|noob|n00b|bro|dude|mate))?",
        stripped,
        flags=re.IGNORECASE,
    )
    if m:
        base = {
            "clear": "не сиди в засаде",
            "live": "не кемпери",
            "raw": "не крысь",
        }.get(style, "не кемпери")
        tails = {
            "idiot": "идиот",
            "noob": "нуб",
            "n00b": "нуб",
            "bro": "братан",
            "dude": "чувак",
            "mate": "бро",
        }
        tail = tails.get((m.group(1) or "").casefold())
        return base + (f", {tail}" if tail else "") + punctuation
    return None


def gaming_slang_transform(text: str, target: str, style: str = "live") -> tuple[str, Optional[str]]:
    """Prepare gaming slang for reliable translation.

    - exact common slang gets a fast human-readable result for RU/EN;
    - slang inside longer messages is expanded in-place before Google Translate;
    - unknown text is left untouched.
    """
    key = normalize_slang_key(text)
    if not key:
        return text, None

    if target == "ru":
        style = style if style in {"clear", "live", "raw"} else "live"
        contextual = _ru_contextual_gaming_phrase(text, style)
        if contextual is not None:
            return text, contextual
        tone_map = RU_GAMING_RAW_DIRECT if style == "raw" else RU_GAMING_LIVE_DIRECT if style == "live" else {}
        if key in tone_map:
            return text, _append_terminal_punctuation(text, tone_map[key])
        if key in RU_GAMING_DIRECT:
            return text, _append_terminal_punctuation(text, RU_GAMING_DIRECT[key])
    if target == "en" and key in EN_FROM_RU_GAMING_DIRECT:
        return text, _append_terminal_punctuation(text, EN_FROM_RU_GAMING_DIRECT[key])

    # Exact English slang going to English is still useful to expand: a user who
    # selected English may not know gamer abbreviations either.
    if target == "en" and key in EN_GAMING_SLANG_EXPANSIONS:
        return text, _append_terminal_punctuation(text, EN_GAMING_SLANG_EXPANSIONS[key])
    if target == "ru" and key in RU_GAMING_SLANG_EXPANSIONS:
        return text, _append_terminal_punctuation(text, RU_GAMING_SLANG_EXPANSIONS[key])

    prepared = _replace_slang_in_text(text, EN_GAMING_SLANG_EXPANSIONS)
    prepared = _replace_slang_in_text(prepared, RU_GAMING_SLANG_EXPANSIONS)
    return prepared, None

def is_map_change_line(line: str) -> bool:
    return line.lstrip().startswith("Server changing map ")


class RecentDuplicateFilter:
    def __init__(self, window_seconds: float = 4.0):
        self.window_seconds = max(0.5, float(window_seconds))
        self.recent: OrderedDict[tuple[str, str], float] = OrderedDict()

    def is_duplicate(self, msg: ChatMessage, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else float(now)
        cutoff = now - self.window_seconds
        while self.recent:
            _key, seen = next(iter(self.recent.items()))
            if seen >= cutoff:
                break
            self.recent.popitem(last=False)
        key = (normalize_for_compare(msg.nickname), normalize_for_compare(msg.text))
        seen = self.recent.get(key)
        self.recent[key] = now
        self.recent.move_to_end(key)
        return seen is not None and seen >= cutoff


def looks_like_target_language(text: str, target: str) -> bool:
    """Cheap pre-check used only for obvious same-language messages.

    The translator still compares source/result after translation, so this helper
    deliberately stays conservative for languages that share an alphabet.
    """
    words = [w.casefold() for w in WORD_RE.findall(text)]
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return True

    if target == "ru":
        # Explicitly avoid treating Ukrainian/Belarusian/Serbian/Macedonian text as Russian.
        if re.search(r"[ІіЇїЄєҐґЎўЈјЉљЊњЋћЂђЏџЃѓЌќЅѕ]", text):
            return False
        cyr = sum(1 for ch in letters if CYRILLIC_RE.fullmatch(ch))
        if cyr / max(len(letters), 1) < 0.90:
            return False
        return any(w in RUSSIAN_HINT_WORDS for w in words)

    # For other target languages, avoid guessing from the Latin alphabet.
    return False


class LogTailer(threading.Thread):
    def __init__(
        self,
        path_getter: Callable[[], Optional[Path]],
        on_message: Callable[[ChatMessage], None],
        on_status: Callable[[str], None],
        stop_event: threading.Event,
        on_control: Optional[Callable[[str, str], None]] = None,
        poll_seconds: float = 0.12,
    ):
        super().__init__(daemon=True, name="cod2-log-tailer")
        self.path_getter = path_getter
        self.on_message = on_message
        self.on_status = on_status
        self.stop_event = stop_event
        self.on_control = on_control
        self.poll_seconds = poll_seconds
        self.current_path: Optional[Path] = None
        self.position = 0
        self.buffer = b""

    def _switch_path(self, path: Path) -> None:
        self.current_path = path
        self.buffer = b""
        try:
            # V1 default: only new chat arriving after the translator starts.
            self.position = path.stat().st_size
            self.on_status(f"Слежу за логом: {path}")
        except FileNotFoundError:
            self.position = 0
            self.on_status("Жду появления console_mp.log…")

    def run(self) -> None:
        while not self.stop_event.is_set():
            path = self.path_getter()
            if path is None:
                self.on_status("Выбери console_mp.log")
                time.sleep(0.5)
                continue

            if self.current_path != path:
                self._switch_path(path)

            try:
                size = path.stat().st_size
                if size < self.position:  # game restarted / log truncated
                    self.position = 0
                    self.buffer = b""

                if size > self.position:
                    with path.open("rb") as fh:
                        fh.seek(self.position)
                        chunk = fh.read(size - self.position)
                        self.position = fh.tell()
                    self.buffer += chunk
                    while b"\n" in self.buffer:
                        raw_line, self.buffer = self.buffer.split(b"\n", 1)
                        line = raw_line.rstrip(b"\r").decode("cp1251", errors="replace")
                        if is_map_change_line(line):
                            if self.on_control:
                                self.on_control("map_change", line)
                            continue
                        msg = parse_chat_line(line)
                        if msg:
                            self.on_message(msg)
                time.sleep(self.poll_seconds)
            except FileNotFoundError:
                self.on_status("Лог пока не найден — жду запуска CoD2…")
                time.sleep(0.5)
            except PermissionError:
                self.on_status("Нет доступа к логу. Запусти переводчик от обычного пользователя.")
                time.sleep(1.0)
            except Exception as exc:
                self.on_status(f"Ошибка чтения лога: {exc}")
                time.sleep(1.0)


class TranslatorWorker(threading.Thread):
    def __init__(
        self,
        jobs: "queue.Queue[ChatMessage]",
        ui_queue: "queue.Queue[tuple]",
        target_getter: Callable[[], str],
        hide_same_getter: Callable[[], bool],
        slang_enabled_getter: Callable[[], bool],
        slang_style_getter: Callable[[], str],
        stop_event: threading.Event,
    ):
        super().__init__(daemon=True, name="translator-worker")
        self.jobs = jobs
        self.ui_queue = ui_queue
        self.target_getter = target_getter
        self.hide_same_getter = hide_same_getter
        self.slang_enabled_getter = slang_enabled_getter
        self.slang_style_getter = slang_style_getter
        self.stop_event = stop_event
        self.cache: OrderedDict[tuple[str, str], str] = OrderedDict()
        self.cache_limit = 400
        self._translator = None
        self._translator_target = None

    @staticmethod
    def _skip_translation(text: str) -> bool:
        stripped = text.strip()
        if len(stripped) <= 1:
            return True
        if not any(ch.isalpha() for ch in stripped):
            return True
        return False

    def _translate(self, text: str, target: str) -> str:
        if self._skip_translation(text):
            return text
        key = (target, text)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]

        from deep_translator import GoogleTranslator

        if self._translator is None or self._translator_target != target:
            self._translator = GoogleTranslator(source="auto", target=target)
            self._translator_target = target

        result = self._translator.translate(text=text) or text
        self.cache[key] = result
        self.cache.move_to_end(key)
        while len(self.cache) > self.cache_limit:
            self.cache.popitem(last=False)
        return result

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                msg = self.jobs.get(timeout=0.2)
            except queue.Empty:
                continue
            target = self.target_getter()
            started = time.monotonic()
            try:
                if self.hide_same_getter() and looks_like_target_language(msg.text, target):
                    self.ui_queue.put(("same_language", msg, 0))
                    continue

                source_text = msg.text
                direct_result = None
                if self.slang_enabled_getter():
                    source_text, direct_result = gaming_slang_transform(msg.text, target, self.slang_style_getter())
                translated = direct_result if direct_result is not None else self._translate(source_text, target)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                if self.hide_same_getter() and normalize_for_compare(translated) == normalize_for_compare(msg.text):
                    self.ui_queue.put(("same_language", msg, elapsed_ms))
                else:
                    self.ui_queue.put(("translation", msg, translated, elapsed_ms))
            except Exception as exc:
                self.ui_queue.put(("translation_error", msg, str(exc)))
            finally:
                self.jobs.task_done()


@dataclass
class OverlayItem:
    nickname: str
    original: str
    translated: str
    created_at: float


def compact_background_size(max_right: int, content_bottom: int, configured_width: int, configured_height: int) -> tuple[int, int]:
    """Return a compact background rectangle around rendered chat content."""
    width = max(70, min(int(configured_width), int(max_right) + 8))
    height = max(28, min(int(configured_height), int(content_bottom) + 3))
    return width, height


def default_overlay_position(screen_width: int, screen_height: int, width: int = 500, height: int = 150) -> tuple[int, int]:
    """Default position chosen from real CoD2 play testing: left side, a little above mid-screen.

    Ratios are used instead of one hard-coded resolution, so 1366x768, 1920x1080
    and other displays start in roughly the same visual place.
    """
    sw = max(640, int(screen_width))
    sh = max(480, int(screen_height))
    x = max(6, round(sw * 0.006))
    y = round(sh * 0.45)
    y = max(40, min(y, sh - max(int(height), 46) - 30))
    return x, y


class OverlayWindow:
    """Two-layer Windows overlay: opaque text above an independently translucent background.

    The text layer uses a chroma-key transparent background, so font readability does
    not change when the user makes the dark background more transparent.  A separate
    click-through background window sits immediately behind the text layer.
    """

    MIN_WIDTH = 200
    MIN_HEIGHT = 46
    TRANSPARENT_KEY = "#010203"

    def __init__(self, root: "tk.Tk", config: dict, on_geometry_changed: Optional[Callable[[], None]] = None, use_fresh_default_position: bool = False):
        self.root = root
        self.config = config
        if use_fresh_default_position:
            overlay = self.config.setdefault("overlay", {})
            width = int(overlay.get("width", 500))
            height = int(overlay.get("height", 150))
            x, y = default_overlay_position(root.winfo_screenwidth(), root.winfo_screenheight(), width, height)
            overlay["x"], overlay["y"] = x, y
        self.on_geometry_changed = on_geometry_changed
        self.items: deque[OverlayItem] = deque()
        self.edit_mode = False
        self._drag_start: Optional[tuple[int, int, int, int]] = None
        self._resize_start: Optional[tuple[int, int, int, int]] = None
        self._actual_height = int(config["overlay"].get("height", 130))
        self._background_width = int(config["overlay"].get("width", 430))
        self._background_height = self._actual_height
        self._fade_alpha = 1.0
        self._fade_job = None
        self._fade_generation = 0

        # Background is a separate window so only the background is translucent.
        self.bg_window = tk.Toplevel(root)
        self.bg_window.withdraw()
        self.bg_window.overrideredirect(True)
        self.bg_window.attributes("-topmost", True)
        self.bg_window.configure(bg="#07111d")

        # Text layer: transparent chroma-key on Windows, fully opaque glyphs.
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=self.TRANSPARENT_KEY)
        if os.name == "nt":
            try:
                self.window.wm_attributes("-transparentcolor", self.TRANSPARENT_KEY)
            except Exception:
                pass

        self.canvas = tk.Canvas(
            self.window,
            bg=self.TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._mouse_down)
        self.canvas.bind("<B1-Motion>", self._mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._mouse_up)
        self.canvas.bind("<Control-MouseWheel>", self._ctrl_wheel)

        self._apply_geometry(force_config_height=True)
        self._set_click_through_window(self.bg_window, True)
        self._set_click_through_window(self.window, True)
        self.window.deiconify()
        self._apply_background_visibility()
        self.render()
        self.root.after(500, self._keep_topmost)

    def _overlay_cfg(self) -> dict:
        return self.config["overlay"]

    def _geometry_values(self, force_config_height: bool = False) -> tuple[int, int, int, int]:
        overlay = self._overlay_cfg()
        x = int(overlay.get("x", 8))
        y = int(overlay.get("y", 360))
        width = max(int(overlay.get("width", 500)), self.MIN_WIDTH)
        config_height = max(int(overlay.get("height", 150)), self.MIN_HEIGHT)
        if force_config_height or self.edit_mode or not overlay.get("auto_height", True):
            height = config_height
        else:
            height = max(self.MIN_HEIGHT, min(self._actual_height, config_height))
        return x, y, width, height

    def _apply_geometry(self, force_config_height: bool = False) -> None:
        x, y, width, height = self._geometry_values(force_config_height=force_config_height)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        if self.edit_mode or not self._overlay_cfg().get("compact_background", True):
            bg_width, bg_height = width, height
        else:
            bg_width = max(1, min(width, int(self._background_width)))
            bg_height = max(1, min(height, int(self._background_height)))
        self.bg_window.geometry(f"{bg_width}x{bg_height}+{x}+{y}")

    def _window_hwnd(self, window: "tk.Toplevel") -> int:
        window.update_idletasks()
        child = int(window.winfo_id())
        if os.name != "nt":
            return child
        try:
            api = _win32_api()
            if not api:
                return child
            user32, _kernel32, _get_long, _set_long = api
            parent = int(user32.GetParent(wintypes.HWND(child)) or 0)
            return parent or child
        except Exception:
            return child

    def _set_click_through_window(self, window: "tk.Toplevel", enabled: bool) -> None:
        if os.name != "nt":
            return
        try:
            hwnd = self._window_hwnd(window)
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            api = _win32_api()
            if not api:
                return
            _user32, _kernel32, get_long, set_long = api
            style = int(get_long(wintypes.HWND(hwnd), GWL_EXSTYLE))
            style |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
            if enabled:
                style |= WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
            else:
                style &= ~WS_EX_TRANSPARENT
                style &= ~WS_EX_NOACTIVATE
            set_long(wintypes.HWND(hwnd), GWL_EXSTYLE, style)
        except Exception:
            pass

    def _force_topmost_window(self, window: "tk.Toplevel") -> None:
        if os.name != "nt":
            try:
                window.attributes("-topmost", True)
                window.lift()
            except Exception:
                pass
            return
        try:
            hwnd = self._window_hwnd(window)
            HWND_TOPMOST = -1
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_SHOWWINDOW = 0x0040
            api = _win32_api()
            if not api:
                return
            user32, _kernel32, _get_long, _set_long = api
            user32.SetWindowPos(
                wintypes.HWND(hwnd), wintypes.HWND(HWND_TOPMOST), 0, 0, 0, 0,
                SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
            )
        except Exception:
            pass

    def _force_topmost_native(self) -> None:
        if self.bg_window.state() != "withdrawn":
            self._force_topmost_window(self.bg_window)
        self._force_topmost_window(self.window)

    def _keep_topmost(self) -> None:
        try:
            if self.window.winfo_exists() and self.window.state() != "withdrawn":
                self._force_topmost_native()
        except Exception:
            return
        self.root.after(500, self._keep_topmost)

    def _background_opacity(self) -> float:
        return max(0.0, min(float(self._overlay_cfg().get("background_opacity", 0.20)), 0.90))

    def _apply_background_visibility(self) -> None:
        opacity = self._background_opacity()
        only_with_messages = bool(self._overlay_cfg().get("background_only_with_messages", True))
        if (
            self.window.state() == "withdrawn"
            or opacity <= 0.001
            or (only_with_messages and not self.items and not self.edit_mode)
        ):
            self.bg_window.withdraw()
            return
        try:
            self.bg_window.attributes("-alpha", opacity * self._fade_alpha)
        except Exception:
            pass
        self.bg_window.deiconify()
        self._set_click_through_window(self.bg_window, True)
        self._force_topmost_native()

    def _set_text_alpha(self, alpha: float) -> None:
        self._fade_alpha = max(0.0, min(float(alpha), 1.0))
        try:
            self.window.attributes("-alpha", self._fade_alpha)
        except Exception:
            pass
        self._apply_background_visibility()

    def _cancel_fade(self) -> None:
        self._fade_generation += 1
        self._fade_job = None

    def _animate_alpha(self, start: float, end: float, duration_ms: int, on_done: Optional[Callable[[], None]] = None) -> None:
        self._fade_generation += 1
        generation = self._fade_generation
        if not self._overlay_cfg().get("fade_enabled", True) or duration_ms <= 0 or self.edit_mode:
            self._set_text_alpha(end)
            if on_done:
                on_done()
            return
        steps = max(4, min(18, int(duration_ms / 25)))
        interval = max(12, int(duration_ms / steps))

        def tick(step: int = 0):
            if generation != self._fade_generation:
                return
            t = min(1.0, step / steps)
            # Smoothstep gives a softer start/end than a linear fade.
            t = t * t * (3.0 - 2.0 * t)
            self._set_text_alpha(start + (end - start) * t)
            if step >= steps:
                self._fade_job = None
                if on_done:
                    on_done()
                return
            self._fade_job = self.root.after(interval, lambda: tick(step + 1))

        tick(0)

    def _fade_in(self) -> None:
        ms = int(self._overlay_cfg().get("fade_ms", 220))
        self._animate_alpha(0.05, 1.0, max(100, ms))

    def _fade_out_and_clear(self) -> None:
        if not self.items:
            return
        ms = int(self._overlay_cfg().get("fade_ms", 220))
        start = self._fade_alpha

        def done():
            self.items.clear()
            self._set_text_alpha(1.0)
            self.render()

        self._animate_alpha(start, 0.0, max(100, ms), on_done=done)

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.window.deiconify()
            self._apply_background_visibility()
            self._force_topmost_native()
        else:
            self.window.withdraw()
            self.bg_window.withdraw()

    def set_edit_mode(self, enabled: bool) -> None:
        self._cancel_fade()
        self._set_text_alpha(1.0)
        self.edit_mode = bool(enabled)
        self._set_click_through_window(self.window, not self.edit_mode)
        self._set_click_through_window(self.bg_window, True)
        self._apply_geometry(force_config_height=self.edit_mode)
        self._apply_background_visibility()
        self._force_topmost_native()
        self.render()

    def set_background_opacity(self, value: float) -> None:
        self._overlay_cfg()["background_opacity"] = max(0.0, min(float(value), 0.90))
        self._apply_background_visibility()
        self.render()

    def set_background_only_with_messages(self, enabled: bool) -> None:
        self._overlay_cfg()["background_only_with_messages"] = bool(enabled)
        self._apply_background_visibility()
        self.render()

    def set_font_size(self, value: int) -> None:
        self._overlay_cfg()["font_size"] = max(7, min(int(value), 20))
        self.render()

    def set_ttl(self, seconds: int) -> None:
        self._overlay_cfg()["message_ttl_seconds"] = max(5, min(int(seconds), 20))

    def set_max_messages(self, count: int) -> None:
        self._overlay_cfg()["max_messages"] = max(1, min(int(count), 3))
        while len(self.items) > self._overlay_cfg()["max_messages"]:
            self.items.popleft()
        self.render()

    def add(self, item: OverlayItem) -> None:
        was_empty = not self.items
        self._cancel_fade()
        self._set_text_alpha(1.0)
        self.items.append(item)
        max_messages = int(self._overlay_cfg().get("max_messages", 3))
        while len(self.items) > max_messages:
            self.items.popleft()
        self.render()
        if was_empty and not self.edit_mode:
            self._fade_in()

    def expire(self) -> None:
        ttl = float(self._overlay_cfg().get("message_ttl_seconds", 11))
        now = time.monotonic()
        expired = 0
        for item in self.items:
            if now - item.created_at > ttl:
                expired += 1
            else:
                break
        if not expired:
            return
        if expired >= len(self.items) and not self.edit_mode:
            # Keep the final message visible while it fades, then clear both
            # text and the compact background together.
            if self._fade_job is None:
                self._fade_out_and_clear()
            return
        for _ in range(expired):
            self.items.popleft()
        self.render()

    def _is_resize_zone(self, x: int, y: int) -> bool:
        _gx, _gy, width, height = self._geometry_values(force_config_height=True)
        return x >= width - 28 and y >= height - 28

    def _mouse_down(self, event) -> None:
        if not self.edit_mode:
            return
        gx, gy, width, height = self._geometry_values(force_config_height=True)
        if self._is_resize_zone(event.x, event.y):
            self._resize_start = (event.x_root, event.y_root, width, height)
        else:
            self._drag_start = (event.x_root, event.y_root, gx, gy)

    def _mouse_move(self, event) -> None:
        if not self.edit_mode:
            return
        overlay = self._overlay_cfg()
        if self._resize_start:
            sx, sy, sw, sh = self._resize_start
            overlay["width"] = max(self.MIN_WIDTH, sw + event.x_root - sx)
            overlay["height"] = max(self.MIN_HEIGHT, sh + event.y_root - sy)
        elif self._drag_start:
            sx, sy, gx, gy = self._drag_start
            overlay["x"] = gx + event.x_root - sx
            overlay["y"] = gy + event.y_root - sy
        self._apply_geometry(force_config_height=True)
        self.render()

    def _mouse_up(self, _event) -> None:
        if not self.edit_mode:
            return
        changed = bool(self._drag_start or self._resize_start)
        self._drag_start = None
        self._resize_start = None
        if changed and self.on_geometry_changed:
            self.on_geometry_changed()

    def _ctrl_wheel(self, event) -> str:
        if not self.edit_mode:
            return "break"
        delta = 1 if event.delta > 0 else -1
        current = int(self._overlay_cfg().get("font_size", 9))
        self.set_font_size(current + delta)
        if self.on_geometry_changed:
            self.on_geometry_changed()
        return "break"

    def _shadowed_text(self, x: int, y: int, *, text: str, fill: str, font, width: int, anchor: str = "nw"):
        # V1.7 uses a real outline instead of a single drop shadow.  With almost
        # no background this keeps letters readable on snow, sky and busy maps.
        radius = 2 if self._background_opacity() <= 0.08 else 1
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        if radius >= 2:
            offsets += [(-2, 0), (2, 0), (0, -2), (0, 2)]
        for dx, dy in offsets:
            self.canvas.create_text(x + dx, y + dy, text=text, anchor=anchor, width=width, fill="#000000", font=font)
        return self.canvas.create_text(x, y, text=text, anchor=anchor, width=width, fill=fill, font=font)

    def render(self) -> None:
        overlay = self._overlay_cfg()
        _x, _y, width, configured_height = self._geometry_values(force_config_height=True)
        self.canvas.delete("all")
        self.canvas.config(width=width, height=configured_height)

        font_size = int(overlay.get("font_size", 9))
        show_original = bool(self.config.get("show_original", False))
        top_pad = 24 if self.edit_mode else 4
        cursor_y = top_pad
        max_right = 0

        if self.edit_mode:
            self.canvas.create_rectangle(1, 1, width - 2, configured_height - 2, outline="#58b7ff", width=2)
            self.canvas.create_rectangle(0, 0, width, 21, fill="#162536", outline="")
            self.canvas.create_text(
                7, 3, text="ПЕРЕТАЩИ • угол ↘ • Ctrl+колесо = шрифт",
                anchor="nw", fill="#d7efff", font=("Segoe UI", 8, "bold"),
            )
            self.canvas.create_polygon(
                width - 22, configured_height - 3,
                width - 3, configured_height - 22,
                width - 3, configured_height - 3,
                fill="#58b7ff", outline="",
            )

        for item in self.items:
            if cursor_y >= configured_height - 12:
                break
            name_font = ("Segoe UI", max(font_size - 2, 7), "bold")
            text_font = ("Segoe UI", font_size)
            original_font = ("Segoe UI", max(font_size - 2, 7))
            wrap_width = max(width - 14, 80)

            name_id = self._shadowed_text(
                7, cursor_y, text=item.nickname, anchor="nw", width=wrap_width,
                fill="#77c7ff", font=name_font,
            )
            bbox = self.canvas.bbox(name_id) or (0, 0, 0, font_size)
            max_right = max(max_right, int(bbox[2]))
            cursor_y = bbox[3]

            tr_id = self._shadowed_text(
                7, cursor_y, text=item.translated, anchor="nw", width=wrap_width,
                fill="#ffffff", font=text_font,
            )
            bbox = self.canvas.bbox(tr_id) or (0, 0, 0, font_size + 2)
            max_right = max(max_right, int(bbox[2]))
            cursor_y = bbox[3] + 2

            if show_original and item.original != item.translated:
                org_id = self._shadowed_text(
                    7, cursor_y, text=item.original, anchor="nw", width=wrap_width,
                    fill="#b8c0c8", font=original_font,
                )
                bbox = self.canvas.bbox(org_id) or (0, 0, 0, font_size)
                max_right = max(max_right, int(bbox[2]))
                cursor_y = bbox[3] + 2
            cursor_y += 3

        if not self.items and self.edit_mode:
            self._shadowed_text(
                7, top_pad + 2, text="CoD2 Translator — жду сообщения…", anchor="nw",
                width=max(width - 14, 80), fill="#b8c0c8", font=("Segoe UI", max(font_size - 1, 7)),
            )
            max_right = min(width - 4, 250)
            cursor_y = top_pad + font_size + 14

        # In play mode shrink vertically to the real content; edit mode keeps the
        # user's configured maximum height so the resize handle stays usable.
        if self.edit_mode or not overlay.get("auto_height", True):
            self._actual_height = configured_height
        else:
            content_height = max(self.MIN_HEIGHT if self.items else 1, cursor_y + 2)
            self._actual_height = min(configured_height, content_height)

        if self.items:
            self._background_width, self._background_height = compact_background_size(
                max_right=max_right, content_bottom=cursor_y, configured_width=width, configured_height=self._actual_height
            )
        else:
            self._background_width = width if self.edit_mode else 1
            self._background_height = configured_height if self.edit_mode else 1

        self._apply_geometry(force_config_height=self.edit_mode)
        self._apply_background_visibility()
        self._force_topmost_native()

def _win32_api():
    """Return Win32 functions with pointer-safe ctypes signatures.

    HWND is pointer-sized on 64-bit Windows.  Calling SetWindowPos/GetWindowLong
    without argtypes can truncate handles when Python itself is 64-bit.  V1.7
    keeps the pointer-safe signatures; this is especially important for CoD2's
    top-level window and the Tk overlay window.
    """
    if os.name != "nt":
        return None

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    LONG_PTR = ctypes.c_ssize_t
    ULONG_PTR = ctypes.c_size_t

    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND

    if hasattr(user32, "GetWindowLongPtrW"):
        get_long = user32.GetWindowLongPtrW
        set_long = user32.SetWindowLongPtrW
    else:  # 32-bit Python
        get_long = user32.GetWindowLongW
        set_long = user32.SetWindowLongW
    get_long.argtypes = [wintypes.HWND, ctypes.c_int]
    get_long.restype = LONG_PTR
    set_long.argtypes = [wintypes.HWND, ctypes.c_int, LONG_PTR]
    set_long.restype = LONG_PTR

    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HANDLE

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    return user32, kernel32, get_long, set_long


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD if os.name == "nt" else ctypes.c_uint32),
        ("rcMonitor", wintypes.RECT if os.name == "nt" else ctypes.c_byte * 16),
        ("rcWork", wintypes.RECT if os.name == "nt" else ctypes.c_byte * 16),
        ("dwFlags", wintypes.DWORD if os.name == "nt" else ctypes.c_uint32),
    ]


def _monitor_rect_for_window(hwnd: int) -> tuple[int, int, int, int]:
    if os.name != "nt":
        return (0, 0, 0, 0)
    api = _win32_api()
    if not api:
        return (0, 0, 0, 0)
    user32, _kernel32, _get_long, _set_long = api
    MONITOR_DEFAULTTONEAREST = 2
    monitor = user32.MonitorFromWindow(wintypes.HWND(hwnd), MONITOR_DEFAULTTONEAREST)
    if monitor:
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_MONITORINFO)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            r = info.rcMonitor
            return int(r.left), int(r.top), int(r.right - r.left), int(r.bottom - r.top)
    return (0, 0, int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1)))


def find_cod2_window() -> Optional[int]:
    """Find the visible CoD2 multiplayer top-level window on Windows."""
    if os.name != "nt":
        return None
    api = _win32_api()
    if not api:
        return None
    user32, kernel32, _get_long, _set_long = api
    found: list[int] = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL

    def process_name(hwnd: int) -> str:
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(handle)
        return ""

    def callback(hwnd, _lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            title_len = user32.GetWindowTextLengthW(hwnd)
            title = ""
            if title_len:
                buf = ctypes.create_unicode_buffer(title_len + 1)
                user32.GetWindowTextW(hwnd, buf, title_len + 1)
                title = buf.value
            exe = process_name(int(hwnd))
            if exe in {"cod2mp_s.exe", "cod2mp.exe", "cod2.exe"}:
                found.append(int(hwnd))
                return False
            low = title.lower()
            if "call of duty 2" in low and "translator" not in low:
                found.append(int(hwnd))
                return False
        except Exception:
            pass
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return found[0] if found else None


def make_cod2_borderless(hwnd: int) -> tuple[bool, str]:
    """Turn an already-windowed CoD2 into borderless fullscreen.

    This does not hook DirectX.  CoD2 must have left exclusive fullscreen first.
    V1.7 also removes TOPMOST from the game itself so the translator overlay can
    remain above it.
    """
    if os.name != "nt" or not hwnd:
        return False, "CoD2 window not available"
    api = _win32_api()
    if not api:
        return False, "Win32 API unavailable"
    user32, _kernel32, get_long, set_long = api

    GWL_STYLE = -16
    GWL_EXSTYLE = -20
    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_SYSMENU = 0x00080000
    WS_POPUP = 0x80000000
    WS_VISIBLE = 0x10000000
    WS_EX_TOPMOST = 0x00000008
    SW_RESTORE = 9
    SWP_FRAMECHANGED = 0x0020
    SWP_SHOWWINDOW = 0x0040
    SWP_NOOWNERZORDER = 0x0200
    HWND_NOTOPMOST = -2

    try:
        ctypes.set_last_error(0)
        user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)

        style = int(get_long(wintypes.HWND(hwnd), GWL_STYLE))
        style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
        style |= WS_POPUP | WS_VISIBLE
        ctypes.set_last_error(0)
        previous = set_long(wintypes.HWND(hwnd), GWL_STYLE, style)
        err = ctypes.get_last_error()
        if previous == 0 and err:
            return False, f"SetWindowLong(style) error {err}"

        exstyle = int(get_long(wintypes.HWND(hwnd), GWL_EXSTYLE))
        exstyle &= ~WS_EX_TOPMOST
        ctypes.set_last_error(0)
        previous = set_long(wintypes.HWND(hwnd), GWL_EXSTYLE, exstyle)
        err = ctypes.get_last_error()
        if previous == 0 and err:
            return False, f"SetWindowLong(exstyle) error {err}"

        left, top, width, height = _monitor_rect_for_window(hwnd)
        ctypes.set_last_error(0)
        ok = user32.SetWindowPos(
            wintypes.HWND(hwnd), wintypes.HWND(HWND_NOTOPMOST),
            left, top, width, height,
            SWP_FRAMECHANGED | SWP_SHOWWINDOW | SWP_NOOWNERZORDER,
        )
        if not ok:
            return False, f"SetWindowPos error {ctypes.get_last_error()}"
        return True, f"{width}×{height} borderless"
    except Exception as exc:
        return False, str(exc)


class ControlApp:
    def __init__(self, root: "tk.Tk"):
        self.root = root
        had_config = config_path().exists() or legacy_config_path().exists()
        self.config = load_config()
        self.fresh_install = not had_config
        self.ui_language = "en" if str(self.config.get("ui_language", installer_language_hint())).lower() == "en" else "ru"
        self.config["ui_language"] = self.ui_language

        # Migrate V1.3 config where opacity meant whole-window opacity.
        overlay_cfg = self.config.setdefault("overlay", {})
        if "background_opacity" not in overlay_cfg and "opacity" in overlay_cfg:
            overlay_cfg["background_opacity"] = max(0.0, min(float(overlay_cfg.get("opacity", 0.20)) * 0.45, 0.90))
        overlay_cfg.pop("opacity", None)

        self.stop_event = threading.Event()
        self.translation_jobs: "queue.Queue[ChatMessage]" = queue.Queue(maxsize=50)
        self.ui_queue: "queue.Queue[tuple]" = queue.Queue()
        self.enabled = True

        self.log_path_var = tk.StringVar(value=self.config.get("log_path", ""))
        self.target_name_var = tk.StringVar(value=self._target_name_for_code(self.config["target_language"]))
        self.show_original_var = tk.BooleanVar(value=bool(self.config.get("show_original", False)))
        self.hide_same_var = tk.BooleanVar(value=bool(self.config.get("hide_same_language", True)))
        self.slang_var = tk.BooleanVar(value=bool(self.config.get("gaming_slang", True)))
        self.slang_style_var = tk.StringVar(value=self._slang_style_name_for_code(self.config.get("slang_style", "live")))
        self.dedupe_var = tk.BooleanVar(value=bool(self.config.get("deduplicate_messages", True)))
        self.ui_language_var = tk.StringVar(value="Русский" if self.ui_language == "ru" else "English")
        self.status_var = tk.StringVar(value=self.t("ready"))
        self.last_var = tk.StringVar(value=self.t("last"))
        self.enabled_var = tk.BooleanVar(value=True)
        self.overlay_editing = False
        self.overlay_hotkey_visible = True
        self._hotkey_prev = {"F8": False}
        self.duplicate_filter = RecentDuplicateFilter(float(self.config.get("duplicate_window_seconds", 4)))
        self.font_var = tk.IntVar(value=int(overlay_cfg.get("font_size", 10)))
        self.bg_var = tk.IntVar(value=round(float(overlay_cfg.get("background_opacity", 0.15)) * 100))
        self.bg_only_var = tk.BooleanVar(value=bool(overlay_cfg.get("background_only_with_messages", True)))
        self.compact_bg_var = tk.BooleanVar(value=bool(overlay_cfg.get("compact_background", True)))
        self.fade_var = tk.BooleanVar(value=bool(overlay_cfg.get("fade_enabled", True)))
        self.ttl_var = tk.IntVar(value=int(overlay_cfg.get("message_ttl_seconds", 10)))
        self.max_messages_var = tk.IntVar(value=int(overlay_cfg.get("max_messages", 2)))
        self.font_label_var = tk.StringVar(value=str(self.font_var.get()))
        self.bg_label_var = tk.StringVar(value=f"{self.bg_var.get()}%")
        self.ttl_label_var = tk.StringVar(value=f"{self.ttl_var.get()} {'с' if self.ui_language == 'ru' else 's'}")

        root.title(f"{APP_NAME} v{APP_VERSION}")
        root.geometry("1030x650")
        root.minsize(900, 560)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._set_window_icon()

        self._build_ui()
        self.overlay = OverlayWindow(root, self.config, on_geometry_changed=self._on_overlay_geometry_changed, use_fresh_default_position=self.fresh_install)
        if self.fresh_install:
            self._persist_settings()

        self.tailer = LogTailer(
            path_getter=self.current_log_path,
            on_message=self.on_log_message,
            on_status=lambda s: self.ui_queue.put(("status", s)),
            stop_event=self.stop_event,
            on_control=lambda kind, line: self.ui_queue.put((kind, line)),
        )
        self.translator = TranslatorWorker(
            jobs=self.translation_jobs,
            ui_queue=self.ui_queue,
            target_getter=self.target_code,
            hide_same_getter=lambda: bool(self.hide_same_var.get()),
            slang_enabled_getter=lambda: bool(self.slang_var.get()),
            slang_style_getter=self.slang_style_code,
            stop_event=self.stop_event,
        )
        self.tailer.start()
        self.translator.start()
        self.root.after(80, self.process_ui_queue)
        self.root.after(500, self.expire_overlay)
        self.root.after(80, self.poll_global_hotkeys)

        if not self.log_path_var.get().strip():
            guess = self.guess_log_path()
            if guess:
                self.log_path_var.set(str(guess))
                self._persist_settings()

        release_cfg = load_release_config(release_config_path())
        if bool(release_cfg.get("check_on_start", True)) and str(release_cfg.get("repository", "")).strip():
            self.root.after(2500, lambda: self.check_updates(manual=False))

    def t(self, key: str) -> str:
        return UI_STRINGS.get(self.ui_language, UI_STRINGS["ru"]).get(key, key)

    def _set_window_icon(self) -> None:
        try:
            ico = resource_path("assets/app.ico")
            if ico.exists():
                self.root.iconbitmap(default=str(ico))
        except Exception:
            pass

    def _style_label(self, code: str) -> str:
        key = {"clear": "style_clear", "live": "style_live", "raw": "style_raw"}.get(code, "style_live")
        return self.t(key)

    def _style_code_from_label(self, label: str) -> str:
        for code in ("clear", "live", "raw"):
            if label == self._style_label(code):
                return code
        return str(self.config.get("slang_style", "live"))

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        try:
            logo = tk.PhotoImage(file=str(resource_path("assets/app_48.png")))
            self._logo_image = logo
            ttk.Label(header, image=logo).pack(side="left", padx=(0, 10))
        except Exception:
            pass
        title_box = ttk.Frame(header)
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="CoD2 Chat Translator", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(title_box, text=self.t("subtitle")).pack(anchor="w", pady=(2, 0))
        ttk.Label(header, text=f"v{APP_VERSION}", foreground="#666666").pack(side="right", anchor="n")

        path_frame = ttk.Frame(outer)
        path_frame.pack(fill="x", pady=(14, 0))
        ttk.Label(path_frame, text=self.t("log"), width=15).pack(side="left")
        ttk.Entry(path_frame, textvariable=self.log_path_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(path_frame, text=self.t("browse"), command=self.choose_log).pack(side="right")

        lang_frame = ttk.Frame(outer)
        lang_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(lang_frame, text=self.t("translate_to"), width=15).pack(side="left")
        custom_label = self._custom_language_label()
        language_values = list(TARGET_LANGUAGES.keys()) + ([custom_label] if custom_label else [])
        self.language_combo = ttk.Combobox(lang_frame, state="readonly", values=language_values, textvariable=self.target_name_var, width=20)
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", lambda _e: self._persist_settings())
        ttk.Button(lang_frame, text=self.t("other"), command=self.choose_custom_language).pack(side="left", padx=(6, 0))
        ttk.Checkbutton(lang_frame, text=self.t("show_original"), variable=self.show_original_var, command=self.toggle_original).pack(side="left", padx=(14, 0))
        ttk.Checkbutton(lang_frame, text=self.t("hide_same"), variable=self.hide_same_var, command=self._persist_settings).pack(side="left", padx=(14, 0))

        smart = ttk.Frame(outer)
        smart.pack(fill="x", pady=(8, 0))
        ttk.Label(smart, text=self.t("smart_chat"), width=15).pack(side="left")
        ttk.Checkbutton(smart, text=self.t("gaming_slang"), variable=self.slang_var, command=self._persist_settings).pack(side="left")
        ttk.Label(smart, text=self.t("style")).pack(side="left", padx=(10, 4))
        style_values = [self._style_label(code) for code in ("clear", "live", "raw")]
        self.slang_style_var.set(self._style_label(str(self.config.get("slang_style", "live"))))
        slang_combo = ttk.Combobox(smart, state="readonly", values=style_values, textvariable=self.slang_style_var, width=14)
        slang_combo.pack(side="left")
        slang_combo.bind("<<ComboboxSelected>>", lambda _e: self._persist_settings())
        ttk.Checkbutton(smart, text=self.t("dedupe"), variable=self.dedupe_var, command=self._persist_settings).pack(side="left", padx=(12, 0))
        ttk.Label(smart, text=self.t("hotkey"), foreground="#666666").pack(side="left", padx=(12, 0))

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(12, 0))
        ttk.Checkbutton(controls, text=self.t("enabled"), variable=self.enabled_var, command=self.toggle_enabled).pack(side="left")
        ttk.Button(controls, text=self.t("test"), command=self.test_overlay).pack(side="left", padx=(12, 0))
        ttk.Button(controls, text=self.t("clear"), command=self.clear_overlay).pack(side="left", padx=(6, 0))
        self.overlay_edit_button = ttk.Button(controls, text=self.t("configure_overlay"), command=self.toggle_overlay_edit)
        self.overlay_edit_button.pack(side="left", padx=(12, 0))
        ttk.Button(controls, text=self.t("cod2_top"), command=self.enable_cod2_borderless).pack(side="left", padx=(12, 0))

        box = ttk.LabelFrame(outer, text=self.t("overlay_view"), padding=(10, 8))
        box.pack(fill="x", pady=(12, 0))

        row1 = ttk.Frame(box); row1.pack(fill="x")
        ttk.Label(row1, text=self.t("font_size"), width=18).pack(side="left")
        font_scale = ttk.Scale(row1, from_=7, to=20, orient="horizontal", command=self._font_slider); font_scale.set(self.font_var.get())
        font_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(row1, textvariable=self.font_label_var, width=5, anchor="e").pack(side="left", padx=(8, 0))

        row2 = ttk.Frame(box); row2.pack(fill="x", pady=(6, 0))
        ttk.Label(row2, text=self.t("background"), width=18).pack(side="left")
        bg_scale = ttk.Scale(row2, from_=0, to=90, orient="horizontal", command=self._background_slider); bg_scale.set(self.bg_var.get())
        bg_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(row2, textvariable=self.bg_label_var, width=5, anchor="e").pack(side="left", padx=(8, 0))
        ttk.Checkbutton(row2, text=self.t("bg_only"), variable=self.bg_only_var, command=self._background_only_changed).pack(side="left", padx=(12, 0))
        ttk.Checkbutton(row2, text=self.t("compact_bg"), variable=self.compact_bg_var, command=self._compact_background_changed).pack(side="left", padx=(10, 0))

        row3 = ttk.Frame(box); row3.pack(fill="x", pady=(6, 0))
        ttk.Label(row3, text=self.t("show_for"), width=18).pack(side="left")
        ttl_scale = ttk.Scale(row3, from_=5, to=20, orient="horizontal", command=self._ttl_slider); ttl_scale.set(self.ttl_var.get())
        ttl_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(row3, textvariable=self.ttl_label_var, width=5, anchor="e").pack(side="left", padx=(8, 0))
        ttk.Checkbutton(row3, text=self.t("fade"), variable=self.fade_var, command=self._fade_changed).pack(side="left", padx=(12, 0))

        row4 = ttk.Frame(box); row4.pack(fill="x", pady=(6, 0))
        ttk.Label(row4, text=self.t("messages"), width=18).pack(side="left")
        msg_combo = ttk.Combobox(row4, state="readonly", values=[1, 2, 3], textvariable=self.max_messages_var, width=5)
        msg_combo.pack(side="left"); msg_combo.bind("<<ComboboxSelected>>", lambda _e: self._max_messages_changed())
        ttk.Button(row4, text=self.t("text_only"), command=self.text_only_preset).pack(side="left", padx=(18, 0))
        ttk.Button(row4, text=self.t("minimal"), command=self.minimal_preset).pack(side="left", padx=(6, 0))
        ttk.Button(row4, text=self.t("readable"), command=self.readable_preset).pack(side="left", padx=(6, 0))
        ttk.Button(row4, text=self.t("standard_place"), command=self.reset_overlay_position).pack(side="left", padx=(10, 0))
        ttk.Label(row4, text=self.t("wheel"), foreground="#666666").pack(side="left", padx=(10, 0))

        ttk.Separator(outer).pack(fill="x", pady=12)
        footer_controls = ttk.Frame(outer); footer_controls.pack(fill="x")
        ttk.Label(footer_controls, text=self.t("interface")).pack(side="left")
        ui_combo = ttk.Combobox(footer_controls, state="readonly", values=["Русский", "English"], textvariable=self.ui_language_var, width=12)
        ui_combo.pack(side="left", padx=(6, 14)); ui_combo.bind("<<ComboboxSelected>>", lambda _e: self.change_ui_language())
        ttk.Button(footer_controls, text=self.t("check_updates"), command=lambda: self.check_updates(manual=True)).pack(side="left")
        ttk.Label(footer_controls, text=f"{self.t('updates')}: stable", foreground="#666666").pack(side="left", padx=(10, 0))
        ttk.Button(footer_controls, text=self.t("about"), command=self.show_about).pack(side="right")
        ttk.Label(footer_controls, text=f"v{APP_VERSION} · by {PROJECT_AUTHOR}", foreground="#666666").pack(side="right", padx=(0, 10))

        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(10, 0))
        ttk.Label(outer, textvariable=self.last_var).pack(anchor="w", pady=(5, 0))
        ttk.Label(outer, text=self.t("privacy"), foreground="#555555", wraplength=850).pack(anchor="w", pady=(12, 0))

    def _project_repository(self) -> str:
        try:
            cfg = load_release_config(release_config_path())
            return str(cfg.get("repository", "")).strip()
        except Exception:
            return ""

    def _project_repository_url(self) -> str:
        repo = self._project_repository()
        return f"https://github.com/{repo}" if repo else ""

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self.root)

    def show_about(self) -> None:
        win = tk.Toplevel(self.root)
        win.title(f"{self.t('about')} — {APP_NAME}")
        win.transient(self.root)
        win.resizable(False, False)
        win.grab_set()
        try:
            ico = resource_path("assets/app.ico")
            if ico.exists():
                win.iconbitmap(default=str(ico))
        except Exception:
            pass

        body = ttk.Frame(win, padding=18)
        body.pack(fill="both", expand=True)
        head = ttk.Frame(body)
        head.pack(fill="x")
        try:
            logo = tk.PhotoImage(file=str(resource_path("assets/app_64.png")))
            win._about_logo = logo
            ttk.Label(head, image=logo).pack(side="left", padx=(0, 12))
        except Exception:
            pass
        title = ttk.Frame(head)
        title.pack(side="left", fill="x", expand=True)
        ttk.Label(title, text=APP_NAME, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(title, text=f"Version {APP_VERSION}", foreground="#666666").pack(anchor="w", pady=(3, 0))

        ttk.Separator(body).pack(fill="x", pady=14)
        ttk.Label(body, text=f"{self.t('developer')}: {PROJECT_AUTHOR}", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(body, text=self.t("made_for")).pack(anchor="w", pady=(6, 0))

        links = ttk.Frame(body)
        links.pack(fill="x", pady=(14, 0))
        ttk.Button(links, text=f"{self.t('github')}: @{PROJECT_AUTHOR}", command=lambda: self._open_url(PROJECT_PROFILE_URL)).pack(side="left")
        repo_url = self._project_repository_url()
        star = ttk.Button(links, text=self.t("star_project"), command=lambda: self._open_url(repo_url) if repo_url else None)
        star.pack(side="left", padx=(8, 0))
        if not repo_url:
            star.state(["disabled"])
            ttk.Label(body, text=self.t("repo_pending"), foreground="#777777", wraplength=430).pack(anchor="w", pady=(10, 0))

        ttk.Button(body, text=self.t("close"), command=win.destroy).pack(anchor="e", pady=(16, 0))
        win.update_idletasks()
        x = self.root.winfo_rootx() + max(20, (self.root.winfo_width() - win.winfo_width()) // 2)
        y = self.root.winfo_rooty() + max(20, (self.root.winfo_height() - win.winfo_height()) // 2)
        win.geometry(f"+{x}+{y}")

    def change_ui_language(self) -> None:
        new_lang = "en" if self.ui_language_var.get() == "English" else "ru"
        if new_lang == self.ui_language:
            return
        self.ui_language = new_lang
        self.config["ui_language"] = new_lang
        self._persist_settings()
        try:
            (settings_dir() / "ui_language.txt").write_text(new_lang, encoding="utf-8")
        except Exception:
            pass
        # Rebuild is simplest and keeps every control consistently translated.
        for child in list(self.root.winfo_children()):
            if child is not getattr(self, "overlay", None):
                try:
                    if isinstance(child, (tk.Toplevel,)):
                        continue
                    child.destroy()
                except Exception:
                    pass
        self.ttl_label_var.set(f"{self.ttl_var.get()} {'с' if new_lang == 'ru' else 's'}")
        self.status_var.set(self.t("ready"))
        self.last_var.set(self.t("last"))
        self._build_ui()

    def _custom_language_label(self) -> str:
        code = str(self.config.get("target_language", "ru"))
        if code not in TARGET_LANGUAGES.values():
            prefix = "Другой" if self.ui_language == "ru" else "Other"
            return f"{prefix} ({code})"
        return ""

    def _target_name_for_code(self, code: str) -> str:
        for name, lang_code in TARGET_LANGUAGES.items():
            if lang_code == code:
                return name
        prefix = "Другой" if getattr(self, "ui_language", "ru") == "ru" else "Other"
        return f"{prefix} ({code})" if code else "Русский"

    def target_code(self) -> str:
        selected = self.target_name_var.get()
        if selected in TARGET_LANGUAGES:
            return TARGET_LANGUAGES[selected]
        match = re.fullmatch(r"(?:Другой|Other) \(([^)]+)\)", selected)
        if match:
            return match.group(1)
        return str(self.config.get("target_language", "ru"))

    def choose_custom_language(self) -> None:
        from tkinter import simpledialog
        current = self.target_code()
        code = simpledialog.askstring(
            self.t("custom_language"), self.t("custom_prompt"),
            initialvalue=current if current not in TARGET_LANGUAGES.values() else "", parent=self.root,
        )
        if code is None:
            return
        code = code.strip()
        if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?", code):
            messagebox.showwarning(self.t("custom_language"), self.t("custom_invalid"))
            return
        prefix = "Другой" if self.ui_language == "ru" else "Other"
        label = f"{prefix} ({code})"
        values = list(TARGET_LANGUAGES.keys()) + [label]
        self.language_combo.configure(values=values)
        self.target_name_var.set(label)
        self.config["target_language"] = code
        self._persist_settings()
        self.status_var.set((f"Язык перевода: {code}" if self.ui_language == "ru" else f"Translation language: {code}"))

    def current_log_path(self) -> Optional[Path]:
        raw = self.log_path_var.get().strip()
        return Path(raw) if raw else None

    def guess_log_path(self) -> Optional[Path]:
        candidates = discover_cod2_logs()
        return candidates[0] if candidates else None

    def choose_log(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("choose_log"),
            filetypes=[("CoD2 log", "*.log"), (self.t("all_files"), "*.*")],
        )
        if path:
            self.log_path_var.set(path)
            self._persist_settings()

    def _slang_style_name_for_code(self, code: str) -> str:
        return self._style_label(code)

    def slang_style_code(self) -> str:
        return self._style_code_from_label(self.slang_style_var.get())

    def check_updates(self, manual: bool = True) -> None:
        release_cfg = load_release_config(release_config_path())
        repository = str(release_cfg.get("repository", "")).strip()
        if not repository:
            if manual:
                self.status_var.set(self.t("update_unconfigured"))
            return
        self.status_var.set(self.t("update_checking"))

        def worker() -> None:
            try:
                info = check_github_release(APP_VERSION, repository)
                self.ui_queue.put(("update_result", info, manual))
            except Exception as exc:
                self.ui_queue.put(("update_error_check", str(exc), manual))
        threading.Thread(target=worker, daemon=True, name="UpdateCheck").start()

    def _launch_updater(self, info: UpdateInfo) -> None:
        install_dir = app_dir()
        updater_name = "CoD2ChatTranslatorUpdater.exe"
        main_name = Path(sys.executable).name if getattr(sys, "frozen", False) else "CoD2ChatTranslator.exe"
        try:
            if getattr(sys, "frozen", False):
                source_updater = install_dir / updater_name
                if not source_updater.exists():
                    raise FileNotFoundError(updater_name)
                temp_updater = Path(tempfile.gettempdir()) / f"CoD2ChatTranslatorUpdater_{int(time.time())}.exe"
                shutil.copy2(source_updater, temp_updater)
                cmd = [str(temp_updater)]
            else:
                source = app_dir() / "updater.py"
                cmd = [sys.executable, str(source)]
            cmd += [
                "--pid", str(os.getpid()),
                "--install-dir", str(install_dir),
                "--download-url", info.download_url,
                "--sha256", info.sha256,
                "--main-exe", main_name,
                "--version", info.version,
                "--ui-language", self.ui_language,
            ]
            subprocess.Popen(cmd, cwd=str(install_dir), close_fds=True)
            self.close()
        except Exception as exc:
            messagebox.showerror(APP_NAME, self.t("update_error").format(error=exc))

    def _persist_settings(self) -> None:
        self.config["ui_language"] = self.ui_language
        self.config["log_path"] = self.log_path_var.get().strip()
        self.config["target_language"] = self.target_code()
        self.config["show_original"] = bool(self.show_original_var.get())
        self.config["hide_same_language"] = bool(self.hide_same_var.get())
        self.config["gaming_slang"] = bool(self.slang_var.get())
        self.config["slang_style"] = self.slang_style_code()
        self.config["deduplicate_messages"] = bool(self.dedupe_var.get())
        overlay = self.config.setdefault("overlay", {})
        overlay["background_only_with_messages"] = bool(self.bg_only_var.get())
        overlay["compact_background"] = bool(self.compact_bg_var.get())
        overlay["fade_enabled"] = bool(self.fade_var.get())
        save_config(self.config)

    def _on_overlay_geometry_changed(self) -> None:
        self.font_var.set(int(self.config["overlay"].get("font_size", 9)))
        self.font_label_var.set(str(self.font_var.get()))
        self._persist_settings()

    def _font_slider(self, value) -> None:
        v = max(7, min(20, round(float(value))))
        self.font_var.set(v)
        self.font_label_var.set(str(v))
        if hasattr(self, "overlay"):
            self.overlay.set_font_size(v)
            self._persist_settings()

    def _background_slider(self, value) -> None:
        v = max(0, min(90, round(float(value))))
        self.bg_var.set(v)
        self.bg_label_var.set(f"{v}%")
        if hasattr(self, "overlay"):
            self.overlay.set_background_opacity(v / 100.0)
            self._persist_settings()

    def _background_only_changed(self) -> None:
        enabled = bool(self.bg_only_var.get())
        self.config["overlay"]["background_only_with_messages"] = enabled
        if hasattr(self, "overlay"):
            self.overlay.set_background_only_with_messages(enabled)
        self._persist_settings()
        self.status_var.set("Фон будет появляться только вместе с сообщениями" if enabled else "Фон остаётся видимым постоянно")

    def _compact_background_changed(self) -> None:
        enabled = bool(self.compact_bg_var.get())
        self.config["overlay"]["compact_background"] = enabled
        if hasattr(self, "overlay"):
            self.overlay.render()
        self._persist_settings()
        self.status_var.set("Подложка подстраивается под длину текста" if enabled else "Подложка использует всю ширину оверлея")

    def _fade_changed(self) -> None:
        enabled = bool(self.fade_var.get())
        self.config["overlay"]["fade_enabled"] = enabled
        if hasattr(self, "overlay") and not enabled:
            self.overlay._cancel_fade()
            self.overlay._set_text_alpha(1.0)
        self._persist_settings()
        self.status_var.set("Плавное появление/исчезновение включено" if enabled else "Анимация отключена")

    def _ttl_slider(self, value) -> None:
        v = max(5, min(20, round(float(value))))
        self.ttl_var.set(v)
        self.ttl_label_var.set(f"{v} {'с' if self.ui_language == 'ru' else 's'}")
        if hasattr(self, "overlay"):
            self.overlay.set_ttl(v)
            self._persist_settings()

    def _max_messages_changed(self) -> None:
        v = max(1, min(3, int(self.max_messages_var.get())))
        self.config["overlay"]["max_messages"] = v
        if hasattr(self, "overlay"):
            self.overlay.set_max_messages(v)
        self._persist_settings()

    def _apply_preset(self, *, width: int, height: int, font: int, background: int, messages: int, ttl: int, label: str) -> None:
        overlay = self.config["overlay"]
        overlay.update({"width": width, "height": height, "font_size": font, "background_opacity": background / 100.0, "background_only_with_messages": True, "compact_background": True, "fade_enabled": True, "max_messages": messages, "message_ttl_seconds": ttl, "auto_height": True})
        self.bg_only_var.set(True)
        self.compact_bg_var.set(True)
        self.fade_var.set(True)
        self.font_var.set(font); self.font_label_var.set(str(font))
        self.bg_var.set(background); self.bg_label_var.set(f"{background}%")
        self.max_messages_var.set(messages)
        self.ttl_var.set(ttl); self.ttl_label_var.set(f"{ttl} {'с' if self.ui_language == 'ru' else 's'}")
        self.overlay._apply_geometry(force_config_height=self.overlay.edit_mode)
        self.overlay.set_font_size(font)
        self.overlay.set_background_opacity(background / 100.0)
        self.overlay.set_max_messages(messages)
        self.overlay.set_ttl(ttl)
        self.overlay.render()
        self._persist_settings()
        self.status_var.set(label)

    def text_only_preset(self) -> None:
        self._apply_preset(width=420, height=120, font=9, background=0, messages=2, ttl=10, label="Только текст: фон полностью прозрачный")

    def minimal_preset(self) -> None:
        self._apply_preset(width=420, height=120, font=9, background=15, messages=2, ttl=10, label="Минимальный: шрифт 9, фон 15%, 2 сообщения")

    def readable_preset(self) -> None:
        self._apply_preset(width=500, height=150, font=10, background=12, messages=2, ttl=10, label="Читаемый: шрифт 10, фон 12%, компактная подложка, 2 сообщения")

    def reset_overlay_position(self) -> None:
        overlay = self.config["overlay"]
        width = int(overlay.get("width", 500))
        height = int(overlay.get("height", 150))
        x, y = default_overlay_position(self.root.winfo_screenwidth(), self.root.winfo_screenheight(), width, height)
        overlay["x"], overlay["y"] = x, y
        self.overlay._apply_geometry(force_config_height=self.overlay.edit_mode)
        self.overlay._force_topmost_native()
        self._persist_settings()
        self.status_var.set("Оверлей возвращён в стандартное место слева")

    def toggle_overlay_edit(self) -> None:
        self.overlay_editing = not self.overlay_editing
        self.overlay.set_edit_mode(self.overlay_editing)
        if self.overlay_editing:
            self.overlay_edit_button.configure(text=self.t("lock_overlay"))
            self.status_var.set("Настройка: перетаскивай окно, тяни угол ↘; Ctrl+колесо меняет шрифт")
            if not self.overlay.items:
                self.test_overlay()
        else:
            self.overlay_edit_button.configure(text=self.t("configure_overlay"))
            self._persist_settings()
            self.status_var.set("Оверлей зафиксирован: мышь проходит сквозь него")

    def enable_cod2_borderless(self) -> None:
        if os.name != "nt":
            self.status_var.set("Borderless helper доступен только в Windows")
            return
        hwnd = find_cod2_window()
        if not hwnd:
            self.status_var.set("Окно CoD2 не найдено. Сначала запусти Multiplayer.")
            return
        ok, detail = make_cod2_borderless(hwnd)
        if ok:
            self.overlay.set_visible(self.enabled)
            self.overlay._force_topmost_native()
            self.status_var.set(f"CoD2 в borderless ({detail}). Оверлей поднят поверх игры.")
        else:
            self.status_var.set(f"Не удалось переключить CoD2: {detail}. Если игра exclusive fullscreen — /r_fullscreen 0 и /vid_restart.")

    def toggle_original(self) -> None:
        self.config["show_original"] = bool(self.show_original_var.get())
        self._persist_settings()
        self.overlay.render()

    def toggle_enabled(self) -> None:
        self.enabled = bool(self.enabled_var.get())
        self.overlay.set_visible(self.enabled and self.overlay_hotkey_visible)
        self.status_var.set(("Переводчик включён" if self.enabled else "Переводчик выключен") if self.ui_language == "ru" else ("Translator enabled" if self.enabled else "Translator disabled"))

    def toggle_overlay_hotkey_visibility(self) -> None:
        self.overlay_hotkey_visible = not self.overlay_hotkey_visible
        self.overlay.set_visible(self.enabled and self.overlay_hotkey_visible)
        self.status_var.set(("F8: оверлей показан" if self.overlay_hotkey_visible else "F8: оверлей скрыт (перевод продолжается)") if self.ui_language == "ru" else ("F8: overlay shown" if self.overlay_hotkey_visible else "F8: overlay hidden (translation continues)"))

    def poll_global_hotkeys(self) -> None:
        if self.stop_event.is_set():
            return
        if os.name == "nt":
            try:
                user32 = ctypes.WinDLL("user32", use_last_error=True)
                user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
                user32.GetAsyncKeyState.restype = ctypes.c_short
                keys = {"F8": 0x77}
                for name, vk in keys.items():
                    down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                    if down and not self._hotkey_prev[name]:
                        self.toggle_overlay_hotkey_visibility()
                    self._hotkey_prev[name] = down
            except Exception:
                pass
        self.root.after(80, self.poll_global_hotkeys)

    def test_overlay(self) -> None:
        self.overlay.add(OverlayItem(nickname="TEST_PLAYER", original="cover me, I go left", translated="прикрой меня, я иду слева", created_at=time.monotonic()))

    def clear_overlay(self) -> None:
        self.overlay._cancel_fade()
        self.overlay.items.clear()
        self.overlay._set_text_alpha(1.0)
        self.overlay.render()

    def on_log_message(self, msg: ChatMessage) -> None:
        if not self.enabled:
            return
        if self.dedupe_var.get() and self.duplicate_filter.is_duplicate(msg):
            self.ui_queue.put(("status", f"Повтор пропущен: {msg.nickname}: {msg.text}"))
            return
        try:
            self.translation_jobs.put_nowait(msg)
            self.ui_queue.put(("status", f"Перевожу: {msg.nickname}: {msg.text}"))
        except queue.Full:
            self.ui_queue.put(("status", "Очередь перевода переполнена — пропускаю сообщение"))

    def process_ui_queue(self) -> None:
        try:
            while True:
                item = self.ui_queue.get_nowait()
                event = item[0]
                if event == "status":
                    self.status_var.set(item[1])
                elif event == "map_change":
                    self.overlay._cancel_fade()
                    self.overlay.items.clear()
                    self.overlay._set_text_alpha(1.0)
                    self.overlay.render()
                    self.status_var.set("Смена карты — старые переводы очищены")
                elif event == "translation":
                    _, msg, translated, elapsed_ms = item
                    self.last_var.set(f"{msg.nickname}: {msg.text}  →  {translated}")
                    self.status_var.set(f"Готово за {elapsed_ms} мс")
                    self.overlay.add(OverlayItem(nickname=msg.nickname, original=msg.text, translated=translated, created_at=time.monotonic()))
                elif event == "same_language":
                    _, msg, elapsed_ms = item
                    self.last_var.set(f"{msg.nickname}: {msg.text}  →  уже выбранный язык, не показываю")
                    self.status_var.set("Сообщение уже на выбранном языке — пропущено" if elapsed_ms == 0 else f"Без дублирования ({elapsed_ms} мс)")
                elif event == "translation_error":
                    _, msg, error = item
                    self.status_var.set((f"Перевод недоступен: {error}" if self.ui_language == "ru" else f"Translation unavailable: {error}"))
                    self.overlay.add(OverlayItem(nickname=msg.nickname, original=msg.text, translated=msg.text, created_at=time.monotonic()))
                elif event == "update_result":
                    _, info, manual = item
                    if info is None:
                        if manual:
                            self.status_var.set(self.t("update_none"))
                    else:
                        notes = info.notes_ru if self.ui_language == "ru" else info.notes_en
                        if not notes:
                            notes = ("Исправления и улучшения." if self.ui_language == "ru" else "Fixes and improvements.")
                        prompt = self.t("update_available").format(version=info.version, notes=notes)
                        if messagebox.askyesno(self.t("update_available_title"), prompt, parent=self.root):
                            self._launch_updater(info)
                        else:
                            self.status_var.set((f"Обновление {info.version} отложено" if self.ui_language == "ru" else f"Update {info.version} postponed"))
                elif event == "update_error_check":
                    _, error, manual = item
                    if manual:
                        self.status_var.set(self.t("update_error").format(error=error))
        except queue.Empty:
            pass
        if not self.stop_event.is_set():
            self.root.after(80, self.process_ui_queue)

    def expire_overlay(self) -> None:
        self.overlay.expire()
        if not self.stop_event.is_set():
            self.root.after(500, self.expire_overlay)

    def close(self) -> None:
        self._persist_settings()
        self.stop_event.set()
        try:
            self.overlay.window.destroy()
            self.overlay.bg_window.destroy()
        except Exception:
            pass
        self.root.destroy()

def cli_test_log(path: Path) -> int:
    messages = read_log_messages(path)
    print(f"Parsed {len(messages)} chat messages from {path}")
    for idx, msg in enumerate(messages, 1):
        print(f"{idx:02d}. {msg.nickname}: {msg.text}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--test-log", type=Path, help="Parse a CoD2 log without starting the GUI")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(APP_VERSION)
        return 0
    if args.test_log:
        return cli_test_log(args.test_log)

    if tk is None:
        print("Tkinter is not available in this Python installation.", file=sys.stderr)
        return 2

    root = tk.Tk()
    try:
        ControlApp(root)
        root.mainloop()
        return 0
    except Exception as exc:
        try:
            messagebox.showerror(APP_NAME, str(exc))
        except Exception:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
