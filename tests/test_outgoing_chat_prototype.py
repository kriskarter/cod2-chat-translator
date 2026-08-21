import unittest
from types import SimpleNamespace
from unittest.mock import patch

from outgoing_chat_prototype import (
    KeyboardCapture,
    OutgoingChatPrototype,
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


    def test_embedded_constructor_initializes_route_before_overlay(self):
        class DummyVar:
            def __init__(self, value=""):
                self.value = value

            def get(self):
                return self.value

            def set(self, value):
                self.value = value

        class DummyRoot:
            def after(self, *_args, **_kwargs):
                return None

        def string_var(*, master=None, value=""):
            return DummyVar(value)

        observed = {}

        def fake_build_overlay(instance):
            observed["route"] = instance.route_var.get()
            observed["source"] = instance.source_name_var.get()
            observed["target"] = instance.target_name_var.get()

        with (
            patch(
                "outgoing_chat_prototype.load_outgoing_preferences",
                return_value=("ru", "en"),
            ),
            patch(
                "outgoing_chat_prototype.tk",
                SimpleNamespace(
                    StringVar=string_var,
                ),
            ),
            patch.object(
                KeyboardCapture,
                "start",
                return_value=None,
            ),
            patch.object(
                OutgoingChatPrototype,
                "_build_overlay_window",
                new=fake_build_overlay,
            ),
        ):
            OutgoingChatPrototype(
                root=DummyRoot(),
            )

        self.assertEqual(
            observed["route"],
            "Русский → English",
        )
        self.assertEqual(
            observed["source"],
            "Русский",
        )
        self.assertEqual(
            observed["target"],
            "English",
        )


if __name__ == "__main__":
    unittest.main()
