import unittest
from types import SimpleNamespace
from unittest.mock import patch

from outgoing_chat import (
    KeyboardCapture,
    LIVE_TRANSLATION_DELAY_MS,
    VK_LSHIFT,
    VK_RSHIFT,
    VK_SHIFT,
    apply_keyboard_modifier_state,
    OutgoingChatController,
    default_source_code_from_ui_language,
    language_code_for_name,
    language_name_for_code,
    normalize_outgoing_text,
    translate_outgoing_text,
)


class OutgoingChatControllerTests(unittest.TestCase):
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
            observed["enabled"] = instance.enabled_var.get()

        with (
            patch(
                "outgoing_chat.load_outgoing_preferences",
                return_value=("ru", "en", True),
            ),
            patch(
                "outgoing_chat.tk",
                SimpleNamespace(
                    StringVar=string_var,
                    BooleanVar=string_var,
                ),
            ),
            patch.object(
                KeyboardCapture,
                "start",
                return_value=None,
            ),
            patch.object(
                OutgoingChatController,
                "_build_overlay_window",
                new=fake_build_overlay,
            ),
        ):
            OutgoingChatController(
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
        self.assertTrue(
            observed["enabled"]
        )

    def test_physical_shift_promotes_generic_shift_state(self):
        for physical_shift in (
            VK_LSHIFT,
            VK_RSHIFT,
        ):
            state = [0] * 256

            apply_keyboard_modifier_state(
                state,
                {physical_shift},
            )

            self.assertTrue(
                state[VK_SHIFT] & 0x80
            )


    def test_live_translation_uses_short_debounce(self):
        self.assertGreaterEqual(
            LIVE_TRANSLATION_DELAY_MS,
            250,
        )
        self.assertLessEqual(
            LIVE_TRANSLATION_DELAY_MS,
            600,
        )

    def test_single_enter_sends_ready_live_translation(self):
        controller = OutgoingChatController.__new__(
            OutgoingChatController
        )

        controller.popup_visible = True
        controller.sending_in_progress = False
        controller.buffer = "привет"
        controller.pending_translation = "hello"
        controller.translation_source = "привет"
        controller.translation_in_progress = False
        controller.send_after_translation = False
        controller.translation_after_id = None

        with (
            patch.object(
                controller,
                "_cancel_live_translation",
            ),
            patch.object(
                controller,
                "_begin_send",
            ) as begin_send,
        ):
            controller.submit()

        begin_send.assert_called_once_with(
            "hello"
        )

    def test_enter_waits_for_running_live_translation(self):
        controller = OutgoingChatController.__new__(
            OutgoingChatController
        )

        controller.popup_visible = True
        controller.sending_in_progress = False
        controller.buffer = "привет"
        controller.pending_translation = ""
        controller.translation_source = "привет"
        controller.translation_in_progress = True
        controller.send_after_translation = False
        controller.translation_after_id = None
        controller.preview = SimpleNamespace(
            configure=lambda **_kwargs: None
        )
        controller.hint = SimpleNamespace(
            configure=lambda **_kwargs: None
        )

        with (
            patch.object(
                controller,
                "_cancel_live_translation",
            ),
            patch.object(
                controller,
                "_start_translation",
            ) as start_translation,
        ):
            controller.submit()

        self.assertTrue(
            controller.send_after_translation
        )
        start_translation.assert_not_called()

    def test_enter_starts_immediate_translation_before_debounce(self):
        controller = OutgoingChatController.__new__(
            OutgoingChatController
        )

        controller.popup_visible = True
        controller.sending_in_progress = False
        controller.buffer = "привет"
        controller.pending_translation = ""
        controller.translation_source = ""
        controller.translation_in_progress = False
        controller.send_after_translation = False
        controller.translation_after_id = None
        controller.preview = SimpleNamespace(
            configure=lambda **_kwargs: None
        )
        controller.hint = SimpleNamespace(
            configure=lambda **_kwargs: None
        )

        with (
            patch.object(
                controller,
                "_cancel_live_translation",
            ),
            patch.object(
                controller,
                "_start_translation",
            ) as start_translation,
        ):
            controller.submit()

        self.assertTrue(
            controller.send_after_translation
        )
        start_translation.assert_called_once_with(
            "привет"
        )

    def test_keyboard_capture_can_be_disabled(self):
        import queue

        keyboard = KeyboardCapture(
            queue.Queue()
        )

        keyboard.set_active(True)
        keyboard.set_enabled(False)

        self.assertFalse(keyboard.enabled)
        self.assertFalse(keyboard.active)


if __name__ == "__main__":
    unittest.main()
