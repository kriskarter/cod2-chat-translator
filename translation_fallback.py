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
        return "auto"

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

    if (
        source != "auto"
        and source == target
    ):
        return source_text

    factory = (
        translator_factory
        or new_mymemory_translator
    )

    try:
        translator = factory(
            source,
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
