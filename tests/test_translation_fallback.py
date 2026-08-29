import unittest
from unittest.mock import patch

from translation_fallback import (
    TranslationFallbackError,
    GOOGLE_REQUEST_TIMEOUT,
    GOOGLE_GTX_REQUEST_TIMEOUT,
    MYMEMORY_REQUEST_TIMEOUT,
    _mymemory_language_code,
    looks_like_service_error,
    translate_with_google_fast,
    translate_with_google_gtx,
    translate_with_google_resilient,
    translate_with_mymemory,
    unchanged_translation_needs_fallback,
)


class TranslationFallbackTests(
    unittest.TestCase
):
    def test_google_fast_translation_uses_bounded_timeout(self):
        observed = {}

        class FakeResponse:
            status_code = 200
            text = (
                '<html><body>'
                '<div class="result-container">'
                'Good evening'
                '</div>'
                '</body></html>'
            )

        def fake_get(
            url,
            params=None,
            headers=None,
            timeout=None,
        ):
            observed["url"] = url
            observed["params"] = params
            observed["timeout"] = timeout
            return FakeResponse()

        result = translate_with_google_fast(
            "добрый вечер",
            source="ru",
            target="en",
            request_get=fake_get,
        )

        self.assertEqual(
            result,
            "Good evening",
        )

        self.assertEqual(
            observed["timeout"],
            GOOGLE_REQUEST_TIMEOUT,
        )

        self.assertEqual(
            observed["params"]["sl"],
            "ru",
        )

        self.assertEqual(
            observed["params"]["tl"],
            "en",
        )

    def test_google_gtx_translation_uses_json_route(self):
        observed = {}

        class FakeResponse:
            status_code = 200

            def json(self):
                return [
                    [
                        ["Good ", "Добрый ", None, None],
                        ["evening", "вечер", None, None],
                    ],
                    None,
                    "ru",
                ]

        def fake_get(
            url,
            params=None,
            headers=None,
            timeout=None,
        ):
            observed["url"] = url
            observed["params"] = params
            observed["timeout"] = timeout
            return FakeResponse()

        result = translate_with_google_gtx(
            "добрый вечер",
            source="ru",
            target="en",
            request_get=fake_get,
        )

        self.assertEqual(
            result,
            "Good evening",
        )

        self.assertEqual(
            observed["timeout"],
            GOOGLE_GTX_REQUEST_TIMEOUT,
        )

        self.assertEqual(
            observed["params"]["client"],
            "gtx",
        )

        self.assertEqual(
            observed["params"]["sl"],
            "ru",
        )

        self.assertEqual(
            observed["params"]["tl"],
            "en",
        )

    def test_google_resilient_uses_gtx_after_mobile_failure(self):
        with (
            patch(
                "translation_fallback.translate_with_google_fast",
                side_effect=TranslationFallbackError(
                    "mobile unavailable"
                ),
            ) as mobile,
            patch(
                "translation_fallback.translate_with_google_gtx",
                return_value="Good evening",
            ) as gtx,
        ):
            result = translate_with_google_resilient(
                "добрый вечер",
                source="ru",
                target="en",
            )

        self.assertEqual(
            result,
            "Good evening",
        )

        mobile.assert_called_once_with(
            "добрый вечер",
            source="ru",
            target="en",
        )

        gtx.assert_called_once_with(
            "добрый вечер",
            source="ru",
            target="en",
        )

    def test_google_resilient_fails_only_after_both_routes_fail(self):
        with (
            patch(
                "translation_fallback.translate_with_google_fast",
                side_effect=TranslationFallbackError(
                    "mobile unavailable"
                ),
            ),
            patch(
                "translation_fallback.translate_with_google_gtx",
                side_effect=TranslationFallbackError(
                    "gtx unavailable"
                ),
            ),
        ):
            with self.assertRaises(
                TranslationFallbackError
            ):
                translate_with_google_resilient(
                    "добрый вечер",
                    source="ru",
                    target="en",
                )


    def test_google_fast_rejects_unchanged_source_text(self):
        class FakeResponse:
            status_code = 200
            text = (
                '<div class="result-container">'
                'добрый вечер'
                '</div>'
            )

        with self.assertRaises(
            TranslationFallbackError
        ):
            translate_with_google_fast(
                "добрый вечер",
                source="ru",
                target="en",
                request_get=(
                    lambda *_args, **_kwargs:
                    FakeResponse()
                ),
            )

    def test_direct_mymemory_uses_bounded_timeout(self):
        observed = {}

        class FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "responseData": {
                        "translatedText":
                        "Good evening"
                    },
                    "matches": [],
                }

        def fake_get(
            url,
            params=None,
            headers=None,
            timeout=None,
        ):
            observed["url"] = url
            observed["params"] = params
            observed["timeout"] = timeout
            return FakeResponse()

        result = translate_with_mymemory(
            "добрый вечер",
            source="ru",
            target="en",
            request_get=fake_get,
        )

        self.assertEqual(
            result,
            "Good evening",
        )

        self.assertEqual(
            observed["timeout"],
            MYMEMORY_REQUEST_TIMEOUT,
        )

        self.assertIn(
            "ru",
            observed["params"]["langpair"].lower(),
        )

        self.assertIn(
            "en",
            observed["params"]["langpair"].lower(),
        )


    def test_mymemory_language_mapping(self):
        self.assertTrue(
            _mymemory_language_code(
                "uk"
            ).lower().startswith(
                "uk"
            )
        )

        self.assertTrue(
            _mymemory_language_code(
                "ru"
            ).lower().startswith(
                "ru"
            )
        )

        self.assertTrue(
            _mymemory_language_code(
                "en"
            ).lower().startswith(
                "en"
            )
        )

        self.assertEqual(
            _mymemory_language_code(
                "zh-CN"
            ).lower(),
            "zh-cn",
        )

    def test_auto_source_is_detected_before_mymemory(self):
        observed = {}

        class FakeTranslator:
            def translate(
                self,
                text,
            ):
                return "привет"

        def factory(
            source,
            target,
        ):
            observed["source"] = source
            observed["target"] = target
            return FakeTranslator()

        with patch(
            "translation_fallback.detect_source_language",
            return_value="pl",
        ):
            result = translate_with_mymemory(
                "czesc",
                source="auto",
                target="ru",
                translator_factory=factory,
            )

        self.assertEqual(
            result,
            "привет",
        )

        self.assertEqual(
            observed["source"],
            "pl",
        )

        self.assertEqual(
            observed["target"],
            "ru",
        )


    def test_unchanged_known_language_requires_fallback(self):
        self.assertTrue(
            unchanged_translation_needs_fallback(
                "добрый вечер",
                "добрый вечер",
                source_language="ru",
                target_language="en",
            )
        )

        self.assertFalse(
            unchanged_translation_needs_fallback(
                "добрый вечер",
                "Good evening",
                source_language="ru",
                target_language="en",
            )
        )

    def test_unchanged_same_language_is_allowed(self):
        self.assertFalse(
            unchanged_translation_needs_fallback(
                "привет",
                "привет",
                source_language="ru",
                target_language="ru",
            )
        )

    def test_unchanged_auto_source_can_trigger_fallback(self):
        with patch(
            "translation_fallback.detect_source_language",
            return_value="en",
        ):
            self.assertTrue(
                unchanged_translation_needs_fallback(
                    "good evening",
                    "good evening",
                    source_language="auto",
                    target_language="ru",
                )
            )


    def test_service_error_detection(self):
        self.assertTrue(
            looks_like_service_error(
                "No translation was found "
                "using the current translator. "
                "Try another translator"
            )
        )

        self.assertTrue(
            looks_like_service_error(
                "Error 500 (Server Error). "
                "That's an error. "
                "Please try again later."
            )
        )

        self.assertTrue(
            looks_like_service_error(
                "'AUTO' IS AN INVALID SOURCE LANGUAGE. "
                "EXAMPLE: LANGPAIR=EN|IT USING 2 LETTER ISO "
                "OR RFC3066 LIKE ZH-CN."
            )
        )

        self.assertFalse(
            looks_like_service_error(
                "hello everyone"
            )
        )

    def test_fallback_translation(self):
        class FakeTranslator:
            def translate(
                self,
                text,
            ):
                self.text = text
                return "hello"

        observed = {}

        def factory(
            source,
            target,
        ):
            observed["source"] = source
            observed["target"] = target
            return FakeTranslator()

        result = translate_with_mymemory(
            "привет",
            source="ru",
            target="en",
            translator_factory=factory,
        )

        self.assertEqual(
            result,
            "hello",
        )

        self.assertEqual(
            observed,
            {
                "source": "ru",
                "target": "en",
            },
        )

    def test_fallback_rejects_error_page(self):
        class BrokenTranslator:
            def translate(
                self,
                text,
            ):
                return (
                    "Error 500 "
                    "(Server Error). "
                    "That's an error. "
                    "Please try again later."
                )

        with self.assertRaises(
            TranslationFallbackError
        ):
            translate_with_mymemory(
                "hello",
                source="en",
                target="ru",
                translator_factory=(
                    lambda _source, _target:
                    BrokenTranslator()
                ),
            )

    def test_same_language_skips_network(self):
        result = translate_with_mymemory(
            "Привіт",
            source="uk",
            target="uk",
            translator_factory=(
                lambda *_args:
                self.fail(
                    "network must not run"
                )
            ),
        )

        self.assertEqual(
            result,
            "Привіт",
        )


if __name__ == "__main__":
    unittest.main()
