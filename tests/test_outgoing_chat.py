import unittest
import queue
import threading
from types import SimpleNamespace
from unittest.mock import patch

from outgoing_chat import (
    KeyboardCapture,
    LIVE_TRANSLATION_DELAY_MS,
    VK_LSHIFT,
    VK_RSHIFT,
    VK_SHIFT,
    apply_keyboard_modifier_state,
    configure_keyboard_user32_api,
    foreground_keyboard_layout,
    OutgoingChatController,
    OutgoingTranslationCache,
    OutgoingTranslationDispatcher,
    OutgoingHttpTransport,
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


    def test_outgoing_uses_fallback_when_google_fails(self):
        with (
            patch(
                "outgoing_chat.translate_with_google_fast",
                side_effect=RuntimeError(
                    "google down"
                ),
            ),
            patch(
                "outgoing_chat.translate_with_mymemory",
                return_value="hello everyone",
            ) as fallback,
        ):
            result = translate_outgoing_text(
                "привет всем",
                target="en",
                source_language="ru",
            )

        self.assertEqual(
            result,
            "hello everyone",
        )

        fallback.assert_called_once_with(
            "привет всем",
            source="ru",
            target="en",
        )


    def test_outgoing_falls_back_when_google_returns_source_text(self):
        with (
            patch(
                "outgoing_chat.translate_with_google_fast",
                return_value="добрый вечер",
            ),
            patch(
                "outgoing_chat.translate_with_mymemory",
                return_value="Good evening",
            ) as fallback,
        ):
            result = translate_outgoing_text(
                "добрый вечер",
                target="en",
                source_language="ru",
            )

        self.assertEqual(
            result,
            "Good evening",
        )

        fallback.assert_called_once_with(
            "добрый вечер",
            source="ru",
            target="en",
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


    def test_keyboard_win32_api_has_explicit_handle_signatures(self):
        class FakeFunction:
            def __init__(self, result=None):
                self.result = result
                self.argtypes = None
                self.restype = None
                self.calls = []

            def __call__(self, *args):
                self.calls.append(args)
                return self.result

        class FakeUser32:
            def __init__(self):
                self.GetForegroundWindow = FakeFunction(
                    12345
                )
                self.GetWindowThreadProcessId = FakeFunction(
                    77
                )
                self.GetKeyboardLayout = FakeFunction(
                    0x0000000000000422
                )
                self.GetKeyboardState = FakeFunction(
                    1
                )
                self.ToUnicodeEx = FakeFunction(
                    1
                )

        user32 = FakeUser32()

        configure_keyboard_user32_api(
            user32
        )

        self.assertIsNotNone(
            user32.GetForegroundWindow.restype
        )
        self.assertIsNotNone(
            user32.GetWindowThreadProcessId.restype
        )
        self.assertIsNotNone(
            user32.GetKeyboardLayout.restype
        )
        self.assertIsNotNone(
            user32.ToUnicodeEx.restype
        )

    def test_foreground_keyboard_layout_uses_foreground_thread(self):
        class FakeUser32:
            def __init__(self):
                self.thread_ids = []

            def GetForegroundWindow(self):
                return 12345

            def GetWindowThreadProcessId(
                self,
                hwnd,
                _process_id,
            ):
                self.hwnd = hwnd
                return 77

            def GetKeyboardLayout(
                self,
                thread_id,
            ):
                self.thread_ids.append(
                    thread_id
                )

                if thread_id == 77:
                    return 0x00000422

                return 0x00000409

        user32 = FakeUser32()

        layout = foreground_keyboard_layout(
            user32
        )

        self.assertEqual(
            int(layout) & 0xFFFF,
            0x0422,
        )
        self.assertEqual(
            user32.thread_ids,
            [77],
        )

    def test_foreground_keyboard_layout_has_safe_fallback(self):
        class FakeUser32:
            def GetForegroundWindow(self):
                return 0

            def GetWindowThreadProcessId(
                self,
                _hwnd,
                _process_id,
            ):
                raise AssertionError(
                    "Must not be called"
                )

            def GetKeyboardLayout(
                self,
                thread_id,
            ):
                self.assert_thread = thread_id
                return 0x00000409

        user32 = FakeUser32()

        layout = foreground_keyboard_layout(
            user32
        )

        self.assertEqual(
            int(layout) & 0xFFFF,
            0x0409,
        )
        self.assertEqual(
            user32.assert_thread,
            0,
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

    def test_paste_clipboard_inserts_normalized_text(self):
        controller = OutgoingChatController.__new__(
            OutgoingChatController
        )

        controller.popup_visible = True
        controller.send_after_translation = False
        controller.sending_in_progress = False
        controller.root = SimpleNamespace(
            clipboard_get=lambda: "  привет\nвсем!  "
        )
        controller.preview = SimpleNamespace(
            configure=lambda **_kwargs: None
        )

        with patch.object(
            controller,
            "append_text",
        ) as append_text:
            controller.paste_clipboard()

        append_text.assert_called_once_with(
            "привет всем!"
        )

    def test_empty_clipboard_does_not_insert_text(self):
        controller = OutgoingChatController.__new__(
            OutgoingChatController
        )

        controller.popup_visible = True
        controller.send_after_translation = False
        controller.sending_in_progress = False
        controller.root = SimpleNamespace(
            clipboard_get=lambda: ""
        )
        controller.preview = SimpleNamespace(
            configure=lambda **_kwargs: None
        )

        with patch.object(
            controller,
            "append_text",
        ) as append_text:
            controller.paste_clipboard()

        append_text.assert_not_called()

    def test_keyboard_capture_can_be_disabled(self):
        import queue

        keyboard = KeyboardCapture(
            queue.Queue()
        )

        keyboard.set_active(True)
        keyboard.set_enabled(False)

        self.assertFalse(keyboard.enabled)
        self.assertFalse(keyboard.active)


class F9SpeedAndReliabilityTests(unittest.TestCase):
    def test_dispatcher_drops_stale_pending_drafts_before_enter(self):
        started = queue.Queue()
        completed = queue.Queue()
        release = threading.Event()
        def translate(value):
            started.put(value)
            release.wait(2)
            completed.put(value)
        dispatcher = OutgoingTranslationDispatcher(translate, workers=2)
        try:
            self.assertTrue(dispatcher.submit("draft A"))
            self.assertEqual(started.get(timeout=2), "draft A")
            self.assertTrue(dispatcher.submit("draft B"))
            self.assertEqual(started.get(timeout=2), "draft B")
            dispatcher.submit("obsolete preview")
            dispatcher.submit("final Enter")
            release.set()
            self.assertEqual(
                {completed.get(timeout=2), completed.get(timeout=2),
                 completed.get(timeout=2)},
                {"draft A", "draft B", "final Enter"},
            )
            self.assertTrue(completed.empty())
        finally:
            dispatcher.close()

    def test_dispatcher_bounds_active_workers_and_pending_queue(self):
        blocker = threading.Event()
        running = queue.Queue()
        def blocked(value):
            running.put(value)
            blocker.wait(2)
        dispatcher = OutgoingTranslationDispatcher(blocked, workers=2)
        try:
            dispatcher.submit("one")
            self.assertEqual(running.get(timeout=2), "one")
            dispatcher.submit("two")
            self.assertEqual(running.get(timeout=2), "two")
            for index in range(100):
                dispatcher.submit(str(index))
            self.assertEqual(dispatcher._jobs.qsize(), 1)
            self.assertEqual(len(dispatcher._workers), 2)
        finally:
            blocker.set()
            dispatcher.close()

    def test_translation_cache_only_contains_successful_string(self):
        cache = OutgoingTranslationCache(max_entries=2)
        key = ("привет", "en", "ru", "live", True, True)
        self.assertIsNone(cache.get(key))
        cache.save(key, "hello")
        self.assertEqual(cache.get(key), "hello")
        cache.save(("x",), "x")
        cache.save(("y",), "y")
        self.assertIsNone(cache.get(key))

    def test_http_transport_reuses_only_current_thread_session(self):
        transport = OutgoingHttpTransport()
        created = []
        class FakeSession:
            def __init__(self):
                self.closed = False
                created.append(self)
            def get(self, *_args, **_kwargs):
                return None
            def close(self):
                self.closed = True
        with patch("outgoing_chat.requests.Session", side_effect=FakeSession):
            first = transport.google_get()
            self.assertIs(first.__self__, transport.google_get().__self__)
            worker_ids = queue.Queue()
            def worker():
                second = transport.google_get()
                worker_ids.put(second.__self__)
                transport.close_current_thread()
            t = threading.Thread(target=worker)
            t.start()
            t.join(timeout=2)
            self.assertFalse(t.is_alive())
            second_session = worker_ids.get_nowait()
            self.assertIsNot(first.__self__, second_session)
            self.assertTrue(second_session.closed)
            transport.close_current_thread()
            self.assertTrue(first.__self__.closed)
        self.assertEqual(len(created), 2)

    def test_f9_worker_snapshots_ui_settings_before_network_thread(self):
        controller = OutgoingChatController.__new__(OutgoingChatController)
        controller.translation_request_id = 0
        controller.translation_source = ""
        controller.pending_translation = ""
        controller.translation_in_progress = False
        controller.send_after_translation = False
        controller.target_code = "en"
        controller.source_code = "ru"
        controller._f9_dispatcher = None
        controller._f9_cache = OutgoingTranslationCache()
        controller._f9_transport = OutgoingHttpTransport()
        controller.legacy_transform = None
        controller.events = queue.Queue()
        controller.preview = SimpleNamespace(configure=lambda **_: None)
        owner_thread = threading.current_thread()
        def on_ui_thread(value):
            self.assertIs(threading.current_thread(), owner_thread)
            return value
        controller.style_getter = lambda: on_ui_thread("live")
        controller.slang_enabled_getter = lambda: on_ui_thread(True)
        controller.smart_enabled_getter = lambda: on_ui_thread(True)
        calls = []
        def fake_translate(text, target, source, **kwargs):
            calls.append((text, target, source, kwargs))
            return "hello"
        try:
            with patch("outgoing_chat.translate_outgoing_text",
                       side_effect=fake_translate):
                controller._start_translation("привет")
                event, data = controller.events.get(timeout=2)
                self.assertEqual(event, "translation_ok")
                self.assertEqual(data[2], "hello")
                self.assertEqual(calls[0][:3], ("привет", "en", "ru"))
                self.assertEqual(calls[0][3]["style"], "live")
                self.assertEqual(calls[0][3]["slang_enabled"], True)
                # Repeated phrases hit the in-memory success cache.
                controller._start_translation("привет")
                self.assertEqual(controller.events.get(timeout=2)[0],
                                 "translation_ok")
                self.assertEqual(len(calls), 1)
        finally:
            if controller._f9_dispatcher:
                controller._f9_dispatcher.close()

    def test_google_failure_uses_cached_mymemory_http_transport(self):
        transport = OutgoingHttpTransport()
        diagnostics = {}
        with (patch("outgoing_chat.translate_with_google_fast",
                    side_effect=RuntimeError("timed out")) as google,
              patch("outgoing_chat.translate_with_mymemory",
                    return_value="good evening") as backup):
            result = translate_outgoing_text(
                "добрый вечер", target="en", source_language="ru",
                slang_enabled=False, transport=transport,
                diagnostics=diagnostics,
            )
        transport.close_current_thread()
        self.assertEqual(result, "good evening")
        self.assertEqual(diagnostics["provider"], "MyMemory")
        self.assertIn("google_ms", diagnostics)
        self.assertIn("fallback_ms", diagnostics)
        self.assertIn("request_get", google.call_args.kwargs)
        self.assertIn("request_get", backup.call_args.kwargs)

    def test_both_free_providers_fail_error_explains_not_sent(self):
        with (patch("outgoing_chat.translate_with_google_fast",
                    side_effect=RuntimeError("timed out")),
              patch("outgoing_chat.translate_with_mymemory",
                    side_effect=RuntimeError("timed out"))):
            with self.assertRaisesRegex(RuntimeError, "Текст не отправлен"):
                translate_outgoing_text(
                    "привет всем", target="en", source_language="ru",
                    slang_enabled=False,
                )

    def test_f9_error_is_visible_and_never_auto_sends(self):
        controller = OutgoingChatController.__new__(OutgoingChatController)
        controller.events = queue.Queue()
        controller.root = SimpleNamespace(after=lambda *_: None)
        controller.translation_request_id = 42
        controller.popup_visible = True
        controller.buffer = "привет всем"
        controller.send_after_translation = True
        controller.translation_in_progress = True
        controller.pending_translation = ""
        captured = {}
        controller.status_var = SimpleNamespace(set=lambda value: captured.__setitem__("status", value))
        controller.preview = SimpleNamespace(configure=lambda **kw: captured.__setitem__("preview", kw))
        controller.hint = SimpleNamespace(configure=lambda **kw: captured.__setitem__("hint", kw))
        controller.events.put((
            "translation_error",
            (42, "привет всем", "Не отвечает Google/MyMemory", 2150, "онлайн-сервисы"),
        ))
        with patch.object(controller, "_begin_send") as send:
            controller._poll_events()
        send.assert_not_called()
        self.assertFalse(controller.send_after_translation)
        self.assertFalse(controller.translation_in_progress)
        self.assertIn("нет перевода", captured["status"])
        self.assertIn("Ничего не отправлено", captured["status"])
        self.assertIn("Не отвечает", captured["preview"]["text"])
        self.assertIn("повторить", captured["hint"]["text"])

    def test_outdated_f9_completion_not_sent_after_user_changed_text(self):
        controller = OutgoingChatController.__new__(OutgoingChatController)
        controller.events = queue.Queue()
        controller.root = SimpleNamespace(after=lambda *_: None)
        controller.translation_request_id = 43
        controller.popup_visible = True
        controller.buffer = "привет и пока"
        controller.send_after_translation = False
        controller.pending_translation = ""
        controller.events.put((
            "translation_ok",
            (42, "привет", "hello", 1200, "Google"),
        ))
        with patch.object(controller, "_begin_send") as send:
            controller._poll_events()
        send.assert_not_called()
        self.assertFalse(controller.pending_translation)

    def test_switching_f9_languages_invalidates_preview(self):
        controller = OutgoingChatController.__new__(OutgoingChatController)
        controller.popup_visible = True
        controller.sending_in_progress = False
        controller.send_after_translation = False
        controller.translation_request_id = 5
        controller.translation_in_progress = True
        controller.pending_translation = "old translation"
        controller.translation_source = "привет"
        controller.buffer = "привет"
        controller.source_name_var = SimpleNamespace(get=lambda: "Русский")
        controller.target_name_var = SimpleNamespace(get=lambda: "Polski")
        controller.enabled = True
        controller.route_var = SimpleNamespace(set=lambda *_: None)
        controller.status_var = SimpleNamespace(set=lambda *_: None)
        with (patch("outgoing_chat.save_outgoing_preferences"),
              patch.object(controller, "_schedule_live_translation") as schedule):
            controller._languages_changed()
        self.assertEqual(controller.target_code, "pl")
        self.assertEqual(controller.translation_request_id, 6)
        self.assertEqual(controller.pending_translation, "")
        self.assertEqual(controller.translation_source, "")
        schedule.assert_called_once()

    def test_mymemory_source_text_is_not_sent_as_translation(self):
        with (patch("outgoing_chat.translate_with_google_fast",
                    side_effect=RuntimeError("timed out")),
              patch("outgoing_chat.translate_with_mymemory",
                    return_value="привет всем")):
            with self.assertRaisesRegex(RuntimeError, "Текст не отправлен"):
                translate_outgoing_text(
                    "привет всем", target="en", source_language="ru",
                    slang_enabled=False,
                )


if __name__ == "__main__":
    unittest.main()
