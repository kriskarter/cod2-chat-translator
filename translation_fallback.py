from __future__ import annotations

import re
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup


class TranslationFallbackError(RuntimeError):
    """Both the primary and fallback translation path failed."""


GOOGLE_MOBILE_URL = (
    "https://translate.google.com/m"
)

GOOGLE_GTX_URL = (
    "https://translate.googleapis.com/"
    "translate_a/single"
)

MYMEMORY_URL = (
    "https://api.mymemory.translated.net/get"
)

# Gameplay must not wait several seconds for a broken
# translation endpoint.
GOOGLE_REQUEST_TIMEOUT = (
    0.40,  # connect
    0.70,  # read
)

# Second Google route. Give it slightly more room than the
# ultra-fast mobile attempt, but still keep gameplay responsive.
GOOGLE_GTX_REQUEST_TIMEOUT = (
    0.60,  # connect
    1.20,  # read
)

# MyMemory is the final independent online fallback.
MYMEMORY_REQUEST_TIMEOUT = (
    0.65,  # connect
    1.30,  # read
)

TRANSLATION_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    ),
}


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


def translate_with_google_fast(
    text: str,
    source: str,
    target: str,
    request_get=None,
    timeout=GOOGLE_REQUEST_TIMEOUT,
) -> str:
    """
    Fast bounded Google mobile translation.

    deep-translator uses the same public Google mobile
    endpoint but does not set a requests timeout.
    For a game overlay we prefer a quick fallback instead
    of blocking for several seconds.
    """

    source_text = str(
        text or ""
    ).strip()

    if not source_text:
        raise TranslationFallbackError(
            "Empty Google translation source"
        )

    if (
        source != "auto"
        and source == target
    ):
        return source_text

    getter = request_get or requests.get

    try:
        response = getter(
            GOOGLE_MOBILE_URL,
            params={
                "sl": source,
                "tl": target,
                "q": source_text,
            },
            headers=TRANSLATION_HTTP_HEADERS,
            timeout=timeout,
        )

        status = int(
            getattr(
                response,
                "status_code",
                200,
            )
            or 200
        )

        if status >= 400:
            raise TranslationFallbackError(
                f"Google HTTP {status}"
            )

        page = str(
            getattr(
                response,
                "text",
                "",
            )
            or ""
        )

        if not page:
            raise TranslationFallbackError(
                "Google returned empty page"
            )

        soup = BeautifulSoup(
            page,
            "html.parser",
        )

        element = soup.find(
            "div",
            {"class": "result-container"},
        )

        if element is None:
            element = soup.find(
                "div",
                {"class": "t0"},
            )

        if element is None:
            raise TranslationFallbackError(
                "Google translation not found"
            )

        result = str(
            element.get_text(
                strip=True
            )
            or ""
        ).strip()

        if looks_like_service_error(
            result
        ):
            raise TranslationFallbackError(
                "Google returned invalid response"
            )

        if unchanged_translation_needs_fallback(
            source_text,
            result,
            source_language=source,
            target_language=target,
        ):
            raise TranslationFallbackError(
                "Google returned source text"
            )

        return result

    except TranslationFallbackError:
        raise

    except Exception as exc:
        raise TranslationFallbackError(
            "Google translation timeout "
            "or network failure"
        ) from exc


def translate_with_google_gtx(
    text: str,
    source: str,
    target: str,
    request_get=None,
    timeout=GOOGLE_GTX_REQUEST_TIMEOUT,
) -> str:
    """
    Secondary free Google translation route.

    Unlike the mobile HTML endpoint, this endpoint returns JSON.
    Having two different Google routes makes a temporary HTML
    change / slowdown less likely to break gameplay translation.
    """

    source_text = str(
        text or ""
    ).strip()

    if not source_text:
        raise TranslationFallbackError(
            "Empty GTX translation source"
        )

    if (
        source != "auto"
        and source == target
    ):
        return source_text

    getter = request_get or requests.get

    try:
        response = getter(
            GOOGLE_GTX_URL,
            params={
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": source_text,
            },
            headers=TRANSLATION_HTTP_HEADERS,
            timeout=timeout,
        )

        status = int(
            getattr(
                response,
                "status_code",
                200,
            )
            or 200
        )

        if status >= 400:
            raise TranslationFallbackError(
                f"Google GTX HTTP {status}"
            )

        data = response.json()

        if (
            not isinstance(data, list)
            or not data
            or not isinstance(data[0], list)
        ):
            raise TranslationFallbackError(
                "Google GTX returned invalid JSON"
            )

        parts = []

        for item in data[0]:
            if (
                isinstance(item, list)
                and item
                and item[0] is not None
            ):
                parts.append(
                    str(item[0])
                )

        result = "".join(parts).strip()

        if looks_like_service_error(
            result
        ):
            raise TranslationFallbackError(
                "Google GTX returned invalid response"
            )

        if unchanged_translation_needs_fallback(
            source_text,
            result,
            source_language=source,
            target_language=target,
        ):
            raise TranslationFallbackError(
                "Google GTX returned source text"
            )

        return result

    except TranslationFallbackError:
        raise

    except Exception as exc:
        raise TranslationFallbackError(
            "Google GTX timeout or network failure"
        ) from exc


def translate_with_google_resilient(
    text: str,
    source: str,
    target: str,
) -> str:
    """
    Try two independent free Google routes.

    Route 1 stays deliberately very fast. If it is temporarily
    slow or its HTML changes, immediately try the JSON route.
    MyMemory remains outside this helper as the independent
    final fallback used by incoming and outgoing translation.
    """

    first_error = None

    try:
        return translate_with_google_fast(
            text,
            source=source,
            target=target,
        )
    except Exception as exc:
        first_error = exc

    try:
        return translate_with_google_gtx(
            text,
            source=source,
            target=target,
        )
    except Exception as second_error:
        raise TranslationFallbackError(
            "Google translation routes unavailable"
        ) from second_error


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
    request_get=None,
    timeout=MYMEMORY_REQUEST_TIMEOUT,
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

    try:
        if translator_factory is not None:
            translator = translator_factory(
                effective_source,
                target,
            )

            result = translator.translate(
                text=source_text
            )

        else:
            getter = (
                request_get
                or requests.get
            )

            source_code = (
                _mymemory_language_code(
                    effective_source
                )
            )

            target_code = (
                _mymemory_language_code(
                    target
                )
            )

            response = getter(
                MYMEMORY_URL,
                params={
                    "q": source_text,
                    "langpair": (
                        f"{source_code}"
                        "|"
                        f"{target_code}"
                    ),
                },
                headers=TRANSLATION_HTTP_HEADERS,
                timeout=timeout,
            )

            status = int(
                getattr(
                    response,
                    "status_code",
                    200,
                )
                or 200
            )

            if status >= 400:
                raise TranslationFallbackError(
                    f"MyMemory HTTP {status}"
                )

            data = response.json()

            response_data = (
                data.get(
                    "responseData",
                    {}
                )
                if isinstance(
                    data,
                    dict,
                )
                else {}
            )

            result = (
                response_data.get(
                    "translatedText"
                )
                or ""
            )

            if not result:
                matches = (
                    data.get(
                        "matches",
                        []
                    )
                    if isinstance(
                        data,
                        dict,
                    )
                    else []
                )

                for match in matches:
                    if not isinstance(
                        match,
                        dict,
                    ):
                        continue

                    candidate = str(
                        match.get(
                            "translation",
                            "",
                        )
                        or ""
                    ).strip()

                    if candidate:
                        result = candidate
                        break

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

        if unchanged_translation_needs_fallback(
            source_text,
            result,
            source_language=effective_source,
            target_language=target,
        ):
            raise TranslationFallbackError(
                "Fallback returned source text"
            )

        return result

    except TranslationFallbackError:
        raise

    except Exception as exc:
        raise TranslationFallbackError(
            "Fallback translation timeout "
            "or network failure"
        ) from exc
