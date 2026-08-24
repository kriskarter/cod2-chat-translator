from __future__ import annotations

import re
from typing import Callable, Optional


class TranslationFallbackError(RuntimeError):
    """Both the primary and fallback translation path failed."""


def looks_like_service_error(result: object) -> bool:
    """
    Detect HTML / upstream failure text that must never be
    displayed or cached as a translation.
    """

    folded = re.sub(
        r"\s+",
        " ",
        str(result or ""),
    ).strip().casefold()

    if not folded:
        return True

    if (
        "<!doctype html" in folded
        or "<html" in folded
    ):
        return True

    if (
        "no translation was found using "
        "the current translator"
        in folded
    ):
        return True

    mymemory_error_markers = (
        "invalid source language",
        "example: langpair=",
        "using 2 letter iso",
        "rfc3066",
    )

    mymemory_hits = sum(
        1
        for marker in mymemory_error_markers
        if marker in folded
    )

    if mymemory_hits >= 2:
        return True

    markers = (
        "error 500",
        "server error",
        "that's an error",
        "there was an error",
        "please try again later",
        "that's all we know",
    )

    hits = sum(
        1
        for marker in markers
        if marker in folded
    )

    return (
        hits >= 2
        or folded.startswith("error 500")
    )


def detect_source_language(
    text: str,
) -> str:
    """
    Detect the source language locally before using MyMemory.

    Google Translate accepts source="auto", but MyMemory requires
    an explicit language pair. Detection happens locally and does
    not send an additional network request.
    """

    value = str(text or "").strip()

    if not value:
        raise TranslationFallbackError(
            "Cannot detect an empty source language"
        )

    # Strong script hints are more reliable than statistical
    # detection for very short in-game messages.
    if re.search(r"[ІіЇїЄєҐґ]", value):
        return "uk"

    if re.search(r"[А-Яа-яЁё]", value):
        return "ru"

    if re.search(r"[Α-ωΆ-ώ]", value):
        return "el"

    if re.search(r"[\u0600-\u06ff]", value):
        return "ar"

    if re.search(r"[\u0590-\u05ff]", value):
        return "he"

    if re.search(r"[\u0900-\u097f]", value):
        return "hi"

    if re.search(r"[\u0e00-\u0e7f]", value):
        return "th"

    if re.search(r"[\u3040-\u30ff]", value):
        return "ja"

    if re.search(r"[\uac00-\ud7af]", value):
        return "ko"

    if re.search(r"[\u4e00-\u9fff]", value):
        return "zh-cn"

    try:
        from langdetect import (
            DetectorFactory,
            detect,
        )

        # langdetect can otherwise return different results
        # for the same very short text between runs.
        DetectorFactory.seed = 0

        detected = str(
            detect(value)
        ).strip().lower()

        if not detected:
            raise ValueError(
                "empty language result"
            )

        return detected

    except Exception as exc:
        raise TranslationFallbackError(
            "Could not detect source language"
        ) from exc


def unchanged_translation_needs_fallback(
    source_text: str,
    translated_text: str,
    source_language: str,
    target_language: str,
) -> bool:
    """
    Return True when a translator returned the original text
    even though source and target languages are different.

    Some unofficial translation endpoints can fail silently
    and simply return the input text. That must trigger our
    fallback instead of being shown as a valid translation.
    """

    source_value = re.sub(
        r"\s+",
        " ",
        str(source_text or ""),
    ).strip().casefold()

    translated_value = re.sub(
        r"\s+",
        " ",
        str(translated_text or ""),
    ).strip().casefold()

    if not source_value:
        return False

    if source_value != translated_value:
        return False

    if not any(
        ch.isalpha()
        for ch in source_value
    ):
        return False

    effective_source = str(
        source_language or ""
    ).strip().lower()

    target = str(
        target_language or ""
    ).strip().lower()

    if not target:
        return False

    if effective_source == "auto":
        try:
            effective_source = (
                detect_source_language(
                    source_text
                )
            )
        except Exception:
            # If detection is uncertain, do not create
            # a false failure for a valid unchanged word.
            return False

    return (
        bool(effective_source)
        and effective_source != target
    )


def _mymemory_language_code(
    language: str,
) -> str:
    """
    Convert our Google-style language codes to one of the
    RFC3066 codes used by deep-translator's MyMemory backend.

    Examples:
        uk -> uk-UA
        ru -> ru-RU
        en -> en-GB
        zh-CN -> zh-CN
    """

    raw = str(language or "").strip()

    if not raw:
        raise ValueError(
            "Empty language code"
        )

    if raw == "auto":
        raise ValueError(
            "MyMemory requires an explicit "
            "source language"
        )

    aliases = {
        # Google/deep-translator historically uses iw.
        "iw": "he",
    }

    raw = aliases.get(
        raw.casefold(),
        raw,
    )

    from deep_translator.constants import (
        MY_MEMORY_LANGUAGES_TO_CODES,
    )

    values = list(
        MY_MEMORY_LANGUAGES_TO_CODES.values()
    )

    # Prefer an exact regional code first.
    for value in values:
        if value.casefold() == raw.casefold():
            return value

    base = raw.split("-", 1)[0].casefold()

    # Then find a regional version with the same ISO base.
    for value in values:
        value_base = (
            value.split("-", 1)[0].casefold()
        )

        if value_base == base:
            return value

    raise ValueError(
        "MyMemory does not support "
        f"language code: {language}"
    )


def new_mymemory_translator(
    source: str,
    target: str,
):
    from deep_translator import (
        MyMemoryTranslator,
    )

    return MyMemoryTranslator(
        source=_mymemory_language_code(
            source
        ),
        target=_mymemory_language_code(
            target
        ),
    )


def translate_with_mymemory(
    text: str,
    source: str,
    target: str,
    translator_factory: Optional[
        Callable[[str, str], object]
    ] = None,
) -> str:
    """
    Emergency translation path.

    No API key is required. CoD2 chat lines are far below
    MyMemory's 500-byte segment limit in normal gameplay.
    """

    source_text = str(
        text or ""
    ).strip()

    if not source_text:
        raise TranslationFallbackError(
            "Empty translation source"
        )

    effective_source = source

    if source == "auto":
        effective_source = (
            detect_source_language(
                source_text
            )
        )

    if effective_source == target:
        return source_text

    factory = (
        translator_factory
        or new_mymemory_translator
    )

    try:
        translator = factory(
            effective_source,
            target,
        )

        result = translator.translate(
            text=source_text
        )

        result = str(
            result or ""
        ).strip()

        if looks_like_service_error(
            result
        ):
            raise TranslationFallbackError(
                "Fallback returned "
                "an invalid response"
            )

        return result

    except TranslationFallbackError:
        raise

    except Exception as exc:
        raise TranslationFallbackError(
            "Fallback translation "
            "service unavailable"
        ) from exc
