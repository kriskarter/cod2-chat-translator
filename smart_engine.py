"""Smart Engine V1: conservative, low-cost semantic guard for CoD2 chat.

No network access or models here. A caller supplies its existing online translation
provider. V1 deliberately abstains rather than inventing tactical meaning.
The confidence score is a heuristic tier, NOT a statistically calibrated probability.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable

KNOWLEDGE_VERSION = "cod2-smart-v1.0"
STYLES = frozenset({"clear", "live", "raw"})
_DIRECT = {
    "gg": {"ru": "хорошая игра", "en": "good game", "uk": "гарна гра"},
    "gg wp": {"ru": "хорошая игра, хорошо сыграно", "en": "good game, well played", "uk": "гарна гра, добре зіграно"},
    "ggwp": {"ru": "хорошая игра, хорошо сыграно", "en": "good game, well played", "uk": "гарна гра, добре зіграно"},
    "gl hf": {"ru": "удачи, приятной игры", "en": "good luck, have fun", "uk": "успіхів, приємної гри"},
    "glhf": {"ru": "удачи, приятной игры", "en": "good luck, have fun", "uk": "успіхів, приємної гри"},
    "nt": {"ru": "хорошая попытка", "en": "nice try", "uk": "гарна спроба"},
    "wp": {"ru": "хорошо сыграно", "en": "well played", "uk": "добре зіграно"},
    "thx": {"ru": "спасибо", "en": "thanks", "uk": "дякую"},
    "ty": {"ru": "спасибо", "en": "thanks", "uk": "дякую"},
    "afk": {"ru": "отошёл от компьютера", "en": "away from keyboard", "uk": "відійшов від комп'ютера"},
    "brb": {"ru": "скоро вернусь", "en": "be right back", "uk": "скоро повернуся"},
}
_AMBIGUOUS = {"ns", "low", "one", "b", "a", "mid", "cover", "plant", "rotate"}
# Direct translit only when the legacy mapping is explicitly known as
# transliteration, not merely because its result contains Cyrillic.
_TRANSLIT_DIRECT = frozenset({
    "privet", "priv", "zdarova", "zdorova", "zdraste", "spasibo",
    "spas", "poka", "davai", "davaj", "kak dela", "vse horosho",
    "vse normalno", "dobroe utro", "dobriy vecher", "dobry vecher",
    "spokoinoi nochi", "spokoynoy nochi", "idi nahui", "idi nahuy",
    "idi na hui", "blya", "blyat", "nahui", "nahuy",
})
_SAFE_LEGACY_DIRECT = frozenset(_DIRECT) | {
    "sry", "sorry", "pls", "plz", "np", "idk", "omg", "lol", "rofl", "lmao",
    "wtf", "wth", "ffs", "stfu", "fu", "fk", "fck", "fuck", "shit",
    "damn", "bitch", "asshole", "mf", "motherfucker", "hs", "headshot",
    "tdm", "dm", "ctf", "sd", "hq", "tk", "teamkill", "votekick",
    "ggs", "gj", "bg", "gl", "hf", "bbl", "gtg", "g2g", "cya",
    "cu", "tyvm", "tnx", "nvm", "mb", "imo", "imho", "wdym",
    "omw", "rn", "rdy", "bro", "dude", "mate", "ez", "noob",
    "n00b", "ff", "hp", "nade", "smoke", "arty", "ks",
    "rush a", "rush b", "go a", "go b", "go mid", "cover me", "low hp",
    # Keep established Russian gamer shortcuts in F8 and F9.
    "гг", "вп", "нс", "нт", "спс", "сяб", "пж", "плз", "сорян",
    "сори", "прив", "афк", "брб", "хз", "имхо", "норм", "изи",
    "нуб", "тк", "тимкилл", "френдлифаер", "хед", "хедшот",
    "хп", "грен", "смок", "флеш", "раш", "рашить", "пуш",
    "фланг", "мид", "кемпер", "респ", "респавн", "спек",
    "лаги", "арта", "авиа", "серия", "база", "флаг",
}
# Only transparent abbreviation expansion is safe inside arbitrary sentences.
_INLINE = {
    "gg": "good game", "ggwp": "good game, well played",
    "glhf": "good luck have fun", "brb": "be right back",
    "afk": "away from keyboard", "thx": "thanks", "ty": "thanks",
    "nt": "nice try", "wp": "well played",
}
# Preserve exact tactical quantities and original channel/identity text.
_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?|(?<![A-Za-z])\d+(?=hp\b)", re.I)
_WEAPON = re.compile(r"(?<!\w)(?:kar98k|mp40|ppsh|mosin|garand|thompson|springfield|panzerschreck)(?!\w)", re.I)
_URL = re.compile(r"https?://[^\s]+|(?<!\w)(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?", re.I)
_OBJECTIVE = re.compile(r"(?<!\w)[AB](?!\w)", re.I)
_CONTEXT_OBJECTIVE = re.compile(r"\b(?:rush|go|plant|defuse|site|hold|push|stack|bomb|at|to|на|точку|точке)\b", re.I)
_NEGATIVE = {
    "en": re.compile(r"\b(?:not|no|never|without|dont|don't|doesn't|didn't|can't|cannot|won't)\b", re.I),
    "ru": re.compile(r"\b(?:не|нет|нельзя|никогда|без)\b", re.I),
    "uk": re.compile(r"\b(?:не|ні|немає|ніколи|без)\b", re.I),
    "pl": re.compile(r"\b(?:nie|nigdy|bez)\b", re.I),
    "de": re.compile(r"\b(?:nicht|kein|keine|nie|ohne)\b", re.I),
    "es": re.compile(r"\b(?:no|nunca|sin)\b", re.I),
    "fr": re.compile(r"\b(?:ne|pas|jamais|sans)\b", re.I),
}
_WARNING = re.compile(r"\b(?:behind|enemy|incoming|watch|careful|сзади|враг|обережно|uważaj)\b", re.I)
_COMMAND = re.compile(r"^(?:rush|go|hold|push|plant|defuse|cover|stop|run|wait|ид[иём]|давай|беги|бігом)\b", re.I)
_QUESTION = re.compile(r"\?$|^(?:where|who|why|what|how|where's|где|кто|почему|де|хто|czemu)\b", re.I)
_LATIN = re.compile(r"[a-zA-Z]")
_CYRILLIC = re.compile(r"[а-яА-ЯёЁіїєґІЇЄҐ]")
_UK_SPECIFIC = re.compile(r"[іїєґІЇЄҐ]")
_RU_SPECIFIC = re.compile(r"[ыэъёЫЭЪЁ]")
_TOKEN = re.compile(r"(?<!\w)(?:ggwp|glhf|brb|afk|thx|ty|nt|wp|gg)(?!\w)", re.I)
_TERMINAL = re.compile(r"([!?…]+)$")


@dataclass(frozen=True)
class ContextMessage:
    text: str
    nickname: str = ""
    timestamp: float = 0.0


@dataclass(frozen=True)
class TranslationRequest:
    text: str
    target_lang: str
    source_lang: str = "auto"
    style: str = "live"
    direction: str = "incoming"
    context: tuple[ContextMessage, ...] = ()
    nickname: str = ""
    use_slang: bool = True


@dataclass(frozen=True)
class TranslationResult:
    text: str
    safe: bool
    confidence: float
    provider: str
    detected_languages: tuple[str, ...] = ()
    intent: str = "inform"
    uncertainty_reasons: tuple[str, ...] = ()
    latency_ms: float = 0.0
    used_context: bool = False
    knowledge_version: str = KNOWLEDGE_VERSION


def _clean_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold()).strip(" .,!?:;…")


def detect_script_languages(text: str) -> tuple[str, ...]:
    """Conservative script hints, not a universal language detector."""
    languages = []
    if _CYRILLIC.search(text):
        if _UK_SPECIFIC.search(text):
            languages.append("uk")
        elif _RU_SPECIFIC.search(text):
            languages.append("ru")
        else:
            languages.append("cyrillic-unknown")
    if _LATIN.search(text):
        languages.append("latin-unknown")
    return tuple(languages)


def classify_intent(text: str) -> str:
    if _QUESTION.search(text):
        return "question"
    if _WARNING.search(text):
        return "warning"
    if _COMMAND.search(text):
        return "command"
    if _clean_key(text) in {"gg", "gg wp", "ggwp", "ns", "wp", "nt", "gj"}:
        return "praise"
    return "inform"


def _terminal(original: str, translation: str) -> str:
    match = _TERMINAL.search(original.strip())
    if match and not translation.rstrip().endswith(match.group(1)):
        return translation.rstrip() + match.group(1)
    return translation


def _objective_tokens(text: str) -> list[str]:
    if not _CONTEXT_OBJECTIVE.search(text):
        return []
    return [x.upper() for x in _OBJECTIVE.findall(text)]


def semantic_violations(source: str, result: str, target: str) -> tuple[str, ...]:
    """Fail closed on critical, objectively checkable meaning loss.

    The gate does not pretend to detect all mistranslations. Its conservative
    objective check is scoped to unambiguous tactical context.
    """
    issues = []
    source_numbers = _NUMBER.findall(source)
    if source_numbers != _NUMBER.findall(result):
        issues.append("numbers")
    source_objectives = _objective_tokens(source)
    if source_objectives:
        target_objectives = [x.upper() for x in _OBJECTIVE.findall(result)]
        # Require source bombsite labels to survive. Do not reject extra
        # lowercase "a": it is a common article/preposition in many target
        # languages and is not necessarily a second objective.
        if any(target_objectives.count(label) < source_objectives.count(label)
               for label in set(source_objectives)):
            issues.append("objectives")
    if source.strip().endswith("?") and "?" not in result:
        issues.append("question")
    for item in _URL.findall(source):
        if item not in result:
            issues.append("url_or_ip")
            break
    source_weapons = {x.casefold() for x in _WEAPON.findall(source)}
    if source_weapons and not source_weapons.issubset(
            {x.casefold() for x in _WEAPON.findall(result)}):
        issues.append("weapons")
    mentions = re.findall(r"(?<!\w)@[^\s,:;!?]+", source)
    if any(mention not in result for mention in mentions):
        issues.append("mention")
    # A literal negative must not vanish. Skip unsupported language pairs:
    # guessing the negative form would generate false confidence.
    target_base = target.lower().split("-", 1)[0]
    source_has_negation = any(p.search(source) for p in _NEGATIVE.values())
    if source_has_negation and target_base in _NEGATIVE:
        if not _NEGATIVE[target_base].search(result):
            issues.append("negation")
    return tuple(issues)


def _inline_expansion(text: str) -> str:
    return _TOKEN.sub(lambda m: _INLINE[m.group(0).casefold()], text)


def _ns_context(request: TranslationRequest) -> tuple[str | None, bool]:
    """Only disambiguate no-scope when an explicit, same-speaker clue exists."""
    key = _clean_key(request.text)
    if key != "ns":
        return None, False
    if request.context:
        recent = request.context[-1]
        if (recent.nickname and recent.nickname == request.nickname
                and re.search(r"\b(?:noscope|no[ -]?scope)\b", recent.text, re.I)):
            return "noscope", True
    return "nice shot", False


class SmartTranslationEngine:
    def translate(
        self,
        request: TranslationRequest,
        provider: Callable[[str, str, str], str],
        legacy_transform: Callable[[str, str, str], tuple[str, str | None]] | None = None,
    ) -> TranslationResult:
        started = time.monotonic()
        original = request.text.strip()
        if not original:
            raise ValueError("Empty translation source")
        target = request.target_lang
        style = request.style if request.style in STYLES else "live"
        languages = detect_script_languages(original)
        intent = classify_intent(original)
        key = _clean_key(original)
        # Source and target may be the same in outgoing chat; respect the
        # explicit language selection. A mixed-script message is not "same".
        if (request.source_lang == target and len(languages) <= 1):
            return TranslationResult(original, True, 1.0, "same-language", languages, intent)

        def finish(value: str, safe: bool, source: str, reasons=(), used_context=False):
            return TranslationResult(
                value, safe, 0.99 if safe and source == "knowledge" else
                (0.75 if safe else 0.0), source, languages, intent,
                tuple(reasons), (time.monotonic() - started) * 1000,
                used_context,
            )

        # Exact, curated non-tactical forms need no network and have no
        # irreversible normalization. Never use a general phrase as a proxy
        # for an unknown tactical instruction.
        if request.use_slang:
            ns_sense, context_used = _ns_context(request)
            if ns_sense:
                direct = {
                    "nice shot": {"ru": "хороший выстрел", "en": "nice shot", "uk": "гарний постріл"},
                    "noscope": {"ru": "без прицела", "en": "no scope", "uk": "без прицілу"},
                }[ns_sense].get(target)
                if direct:
                    return finish(_terminal(original, direct), True, "knowledge",
                                  used_context=context_used)
            known = _DIRECT.get(key, {}).get(target)
            if known:
                return finish(_terminal(original, known), True, "knowledge")

        # Use the legacy exact-shortcase map only if no risky factual
        # entity is present. It remains a compatibility path, not a mandatory
        # destructive inline preprocessor.
        candidate = original
        if request.use_slang and legacy_transform is not None:
            prepared, direct = legacy_transform(original, target, style)
            if (key in _SAFE_LEGACY_DIRECT and direct is not None
                    and not semantic_violations(original, direct, target)):
                return finish(direct, True, "legacy-direct")
            # Fully recognized translit in the requested target language
            # does not need a paid or slow translation call.
            if (target == "ru" and key in _TRANSLIT_DIRECT
                    and direct is not None and prepared == original
                    and not _CYRILLIC.search(original)
                    and _CYRILLIC.search(direct)
                    and not _NUMBER.search(original)
                    and not _objective_tokens(original)
                    and not semantic_violations(original, direct, target)
                    and key not in _AMBIGUOUS
                    and re.fullmatch(r"[a-zA-Z\s.,!?'…-]+", original)):
                return finish(direct, True, "legacy-translit")
            # Keep conservative fully recognized Cyrillic transliteration,
            # but only when no protected objective/number would be affected.
            if (prepared != original
                    and not _NUMBER.search(original)
                    and not _objective_tokens(original)
                    and not _CYRILLIC.search(original)
                    and re.fullmatch(r"[\w\s.,!?'…-]+", original)
                    and _CYRILLIC.search(prepared)
                    and not semantic_violations(original, prepared, target)):
                candidate = prepared
        # Only expand unambiguous abbreviations; no "low -> HP", no
        # "behind -> enemy", no "1hp -> almost no health".
        if request.use_slang and candidate == original:
            expanded = _inline_expansion(original)
            if expanded != original and not semantic_violations(original, expanded, target):
                candidate = expanded

        # Avoid passing contextual history to arbitrary third-party endpoints.
        # Current online providers only receive this one cleaned chat message.
        translated = str(provider(candidate, target, request.source_lang) or "").strip()
        reasons = semantic_violations(original, translated, target)
        if reasons and candidate != original:
            # Retry with the intact original when normalization was unsafe.
            translated = str(provider(original, target, request.source_lang) or "").strip()
            reasons = semantic_violations(original, translated, target)
        if not translated or reasons:
            # Incoming: caller can show original; outgoing: caller must block
            # automatic send rather than silently sending misleading tactics.
            return finish(original, False, "abstain", reasons or ("empty",))
        return finish(translated, True, "online")


DEFAULT_ENGINE = SmartTranslationEngine()
