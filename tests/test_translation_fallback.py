import unittest

from translation_fallback import (
    TranslationFallbackError,
    _mymemory_language_code,
    looks_like_service_error,
    translate_with_mymemory,
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
