import unittest
from unittest.mock import patch

from translation_fallback import (
    TranslationFallbackError,
    _mymemory_language_code,
    looks_like_service_error,
    translate_with_mymemory,
    unchanged_translation_needs_fallback,
)


class TranslationFallbackTests(
    unittest.TestCase
):
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
