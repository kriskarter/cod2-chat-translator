import unittest

from outgoing_chat_prototype import (
    default_source_code_from_ui_language,
    language_code_for_name,
    language_name_for_code,
    normalize_outgoing_text,
    translate_outgoing_text,
)


class OutgoingChatPrototypeTests(unittest.TestCase):
    def test_normalizes_whitespace(self):
        self.assertEqual(
            normalize_outgoing_text("  привет   всем  "),
            "привет всем",
        )

    def test_preserves_cyrillic_and_punctuation(self):
        self.assertEqual(
            normalize_outgoing_text("спасибо, хороший выстрел :)"),
            "спасибо, хороший выстрел :)",
        )

    def test_multiline_input_becomes_single_chat_line(self):
        self.assertEqual(
            normalize_outgoing_text("привет\nкак дела?"),
            "привет как дела?",
        )


    def test_interface_language_can_seed_my_language(self):
        self.assertEqual(
            default_source_code_from_ui_language("uk"),
            "uk",
        )
        self.assertEqual(
            default_source_code_from_ui_language("en"),
            "en",
        )
        self.assertEqual(
            default_source_code_from_ui_language("unknown"),
            "ru",
        )

    def test_language_name_and_code_mapping(self):
        self.assertEqual(
            language_code_for_name("Українська"),
            "uk",
        )
        self.assertEqual(
            language_name_for_code("de"),
            "Deutsch",
        )

    def test_same_source_and_target_skips_network_translation(self):
        self.assertEqual(
            translate_outgoing_text(
                "  Привіт усім!  ",
                target="uk",
                source_language="uk",
            ),
            "Привіт усім!",
        )


if __name__ == "__main__":
    unittest.main()
