"""Synthetic CoD2 semantic fixtures. No claim these are real server messages."""
import queue
import threading
import unittest
from unittest.mock import patch

from app import (
    ChatMessage, TranslatorWorker, TranslationWorkerSharedState, gaming_slang_transform
)
from smart_engine import (
    KNOWLEDGE_VERSION,
    ContextMessage,
    SmartTranslationEngine,
    TranslationRequest,
    classify_intent,
    detect_script_languages,
    semantic_violations,
)
from translation_fallback import detect_source_language
from outgoing_chat import translate_outgoing_text


class SmartEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = SmartTranslationEngine()
        self.calls = []

    def translate(self, text, target="ru", *, provider=None, **options):
        def fake(value, dest, source):
            self.calls.append((value, dest, source))
            return "принято" if provider is None else provider(value, dest, source)
        return self.engine.translate(
            TranslationRequest(text, target, **options),
            provider=fake,
            legacy_transform=gaming_slang_transform,
        )

    def test_version_is_explicit(self):
        self.assertEqual(KNOWLEDGE_VERSION, "cod2-smart-v1.0")

    def test_known_gg_is_instant_without_network(self):
        result = self.translate("gg!", target="ru")
        self.assertEqual(result.text, "хорошая игра!")
        self.assertEqual(result.provider, "knowledge")
        self.assertTrue(result.safe)
        self.assertEqual(self.calls, [])

    def test_ukrainian_knowledge_is_local(self):
        self.assertEqual(self.translate("nt", target="uk").text, "гарна спроба")
        self.assertEqual(self.calls, [])

    def test_raw_style_of_legacy_direct_is_preserved(self):
        result = self.translate("wtf", style="raw")
        self.assertEqual(result.text, "что за хуйня")
        self.assertEqual(result.provider, "legacy-direct")

    def test_style_clear_differs_from_raw(self):
        result = self.translate("wtf", style="clear")
        self.assertNotIn("хуйня", result.text)

    def test_no_slang_skips_exact_shortcut(self):
        result = self.translate("gg", use_slang=False)
        self.assertEqual(result.text, "принято")
        self.assertEqual(self.calls[0][0], "gg")

    def test_russian_gg_to_english_remains_local(self):
        result = self.translate("гг", target="en")
        self.assertEqual(result.text, "good game")
        self.assertEqual(self.calls, [])

    def test_russian_thanks_to_english_remains_local(self):
        result = self.translate("спс", target="en")
        self.assertEqual(result.text, "thanks")
        self.assertEqual(self.calls, [])

    def test_rush_b_keeps_legacy_tactical_shortcut(self):
        result = self.translate("rush B", target="ru")
        self.assertEqual(result.text, "быстрая атака на B")
        self.assertEqual(self.calls, [])

    def test_translit_fully_recognized_fast(self):
        result = self.translate("privet", target="ru")
        self.assertEqual(result.text, "привет")
        self.assertEqual(result.provider, "legacy-translit")
        self.assertEqual(self.calls, [])

    def test_translit_conservative_for_english(self):
        self.translate("give me cover", target="ru")
        self.assertEqual(self.calls[0][0], "give me cover")

    def test_legacy_must_not_destroy_exact_hp(self):
        result = self.translate("1hp", provider=lambda text, *_: "1 HP")
        self.assertTrue(result.safe)
        self.assertEqual(result.text, "1 HP")
        self.assertEqual(self.calls[0][0], "1hp")

    def test_bad_translation_number_blocks(self):
        result = self.translate("2 hp", provider=lambda *_: "мало здоровья")
        self.assertFalse(result.safe)
        self.assertEqual(result.text, "2 hp")
        self.assertIn("numbers", result.uncertainty_reasons)

    def test_objective_must_survive(self):
        result = self.translate("rush B", provider=lambda *_: "быстро на A",
                                use_slang=False)
        self.assertFalse(result.safe)
        self.assertIn("objectives", result.uncertainty_reasons)

    def test_objective_correct_is_accepted(self):
        result = self.translate("rush B", provider=lambda *_: "быстро на B",
                                use_slang=False)
        self.assertTrue(result.safe)

    def test_question_punctuation_not_dropped(self):
        result = self.translate("where are you?", provider=lambda *_: "ты где")
        self.assertFalse(result.safe)
        self.assertIn("question", result.uncertainty_reasons)

    def test_negation_not_dropped(self):
        result = self.translate("don't rush B", provider=lambda *_: "беги на B")
        self.assertFalse(result.safe)
        self.assertIn("negation", result.uncertainty_reasons)

    def test_negation_supported(self):
        result = self.translate("don't rush B", provider=lambda *_: "не беги на B")
        self.assertTrue(result.safe)

    def test_no_inferred_enemy_behind_you(self):
        result = self.translate("behind you", provider=lambda *_: "позади тебя")
        self.assertTrue(result.safe)
        self.assertEqual(self.calls[0][0], "behind you")
        self.assertNotIn("враг", result.text)

    def test_abbreviation_expanded_nondestructively(self):
        self.translate("gg bro", provider=lambda *_: "хорошая игра, братан")
        self.assertEqual(self.calls[0][0], "good game bro")

    def test_critical_failure_on_normalized_text_retries_original(self):
        def provider(text, *_):
            return "бегом на A" if text != "rush B gg" else "бегом на B, хорошая игра"
        result = self.translate("rush B gg", provider=provider)
        self.assertTrue(result.safe)
        self.assertEqual([x[0] for x in self.calls], ["rush B good game", "rush B gg"])

    def test_unambiguous_ns_defaults_to_nice_shot(self):
        result = self.translate("ns")
        self.assertEqual(result.text, "хороший выстрел")

    def test_same_speaker_context_disambiguates_ns(self):
        context = (ContextMessage("no scope sniper", "Alpha", 0),)
        result = self.translate("ns", context=context, nickname="Alpha")
        self.assertEqual(result.text, "без прицела")
        self.assertTrue(result.used_context)

    def test_other_speaker_context_does_not_leak(self):
        context = (ContextMessage("no scope sniper", "Beta", 0),)
        result = self.translate("ns", context=context, nickname="Alpha")
        self.assertEqual(result.text, "хороший выстрел")
        self.assertFalse(result.used_context)

    def test_dont_confuse_cyrillic_and_latin(self):
        self.assertEqual(detect_script_languages("дружище go B"),
                         ("cyrillic-unknown", "latin-unknown"))

    def test_ukrainian_script(self):
        self.assertEqual(detect_script_languages("привіт"), ("uk",))

    def test_intent_is_conservative(self):
        self.assertEqual(classify_intent("rush B"), "command")
        self.assertEqual(classify_intent("where B?"), "question")
        self.assertEqual(classify_intent("enemy behind"), "warning")

    def test_same_language_explicit(self):
        result = self.translate("привет", source_lang="ru")
        self.assertEqual(result.text, "привет")
        self.assertEqual(self.calls, [])

    def test_preserve_original_when_provider_returns_empty(self):
        result = self.translate("some unknown phrase", provider=lambda *_: "")
        self.assertFalse(result.safe)
        self.assertEqual(result.text, "some unknown phrase")

    def test_mentions_are_protected(self):
        self.assertIn("mention", semantic_violations("@Player wait", "подожди", "ru"))
        self.assertEqual(semantic_violations("@Player wait", "@Player, подожди", "ru"), ())

    def test_mixed_language_is_not_decided_by_one_word(self):
        result = self.translate("privet go B", provider=lambda *_: "привет, иди B")
        self.assertEqual(result.detected_languages, ("latin-unknown",))
        self.assertEqual(self.calls[0][0], "privet go B")


class F9SemanticSafetyTests(unittest.TestCase):
    def test_outgoing_uses_same_local_knowledge(self):
        with patch("outgoing_chat.translate_with_google_fast") as google:
            result = translate_outgoing_text("gg", target="uk", source_language="en")
        self.assertEqual(result, "гарна гра")
        google.assert_not_called()

    def test_outgoing_blocks_corrupt_tactical_number(self):
        with patch("outgoing_chat.translate_with_google_fast", return_value="здоровья мало"):
            with self.assertRaisesRegex(RuntimeError, "безопасно"):
                translate_outgoing_text("1hp", target="ru", source_language="en")

    def test_outgoing_blocks_wrong_objective(self):
        with patch("outgoing_chat.translate_with_google_fast", return_value="иди на A"):
            with self.assertRaisesRegex(RuntimeError, "безопасно"):
                translate_outgoing_text("rush B", target="ru", source_language="en")

    def test_outgoing_preserves_legacy_raw_style(self):
        with patch("outgoing_chat.translate_with_google_fast") as google:
            value = translate_outgoing_text("wtf", target="ru", source_language="en",
                                            style="raw", legacy_transform=gaming_slang_transform)
        self.assertEqual(value, "что за хуйня")
        google.assert_not_called()

    def test_outgoing_legacy_disabled(self):
        with patch("outgoing_chat.translate_with_google_fast", return_value="перевод") as google:
            value = translate_outgoing_text("gg", target="ru", source_language="en",
                                            slang_enabled=False)
        self.assertEqual(value, "перевод")
        google.assert_called_once()

    def test_classic_f9_can_be_restored_immediately(self):
        with patch("outgoing_chat.translate_with_google_fast", return_value="перевод") as google:
            self.assertEqual(
                translate_outgoing_text("gg", target="ru", source_language="en",
                                        smart_enabled=False),
                "перевод",
            )
        google.assert_called_once()

    def test_smart_enabled_by_default_in_config(self):
        from app import DEFAULT_CONFIG
        self.assertTrue(DEFAULT_CONFIG["smart_engine_enabled"])


class F8WorkerIntegrationTests(unittest.TestCase):
    def test_worker_keeps_uncertain_tactics_visible(self):
        tasks, events, stop = queue.Queue(), queue.Queue(), threading.Event()
        worker = TranslatorWorker(tasks, events, lambda: "ru", lambda: True,
                                  lambda: True, lambda: "live", stop)
        def provider(text, target):
            stop.set()
            return "здоровья мало"
        worker._translate = provider
        tasks.put(ChatMessage("Player", "2 hp"))
        worker.start()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        result = events.get_nowait()
        self.assertEqual(result[0], "translation")
        self.assertEqual(result[2], "⚠ 2 hp")

    def test_worker_uses_shared_engine(self):
        tasks, events, stop = queue.Queue(), queue.Queue(), threading.Event()
        worker = TranslatorWorker(tasks, events, lambda: "ru", lambda: False,
                                  lambda: True, lambda: "live", stop)
        def provider(text, target):
            stop.set()
            return "позади тебя"
        worker._translate = provider
        tasks.put(ChatMessage("Player", "behind you"))
        worker.start()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(events.get_nowait()[2], "позади тебя")


    def test_worker_can_restore_classic_direct_translation(self):
        tasks, events, stop = queue.Queue(), queue.Queue(), threading.Event()
        worker = TranslatorWorker(tasks, events, lambda: "ru", lambda: False,
                                  lambda: True, lambda: "live", stop,
                                  smart_enabled_getter=lambda: False)
        tasks.put(ChatMessage("Player", "behind you"))
        stop_hook = worker._translate
        # The legacy exact direct path must not use the online provider.
        worker._translate = lambda *_: self.fail("unexpected network call")
        worker.start()
        self.assertEqual(events.get(timeout=2)[2], "враг сзади")
        stop.set()
        worker.join(2)
        self.assertFalse(worker.is_alive())




class FastIncomingTests(unittest.TestCase):
    def test_shared_cache_between_workers(self):
        shared = TranslationWorkerSharedState()
        jobs, events, stop = queue.Queue(), queue.Queue(), threading.Event()
        def create():
            return TranslatorWorker(
                jobs, events, lambda: "ru", lambda: False,
                lambda: False, lambda: "live", stop,
                shared_state=shared,
            )
        first, second = create(), create()
        class FakeTranslator:
            def __init__(self):
                self.calls = 0

            def translate(self, text):
                self.calls += 1
                return "переведено"

        translator = FakeTranslator()
        first._new_translator = lambda _target: translator
        second._new_translator = lambda _target: translator
        self.assertEqual(first._translate("hello", "ru"), "переведено")
        self.assertEqual(second._translate("hello", "ru"), "переведено")
        self.assertEqual(translator.calls, 1)

    def test_shared_metrics_no_content_logged(self):
        state = TranslationWorkerSharedState()
        state.record(120, 150)
        state.record(200, 200)
        metrics = state.snapshot()
        self.assertEqual(metrics["samples"], 2)
        self.assertEqual(metrics["queue_p95_ms"], 200)
        self.assertEqual(metrics["provider_p50_ms"], 200)
        self.assertNotIn("text", str(metrics))
        self.assertNotIn("nickname", str(metrics))

    def test_worker_reuses_google_http_session(self):
        shared = TranslationWorkerSharedState()
        worker = TranslatorWorker(
            queue.Queue(), queue.Queue(), lambda: "ru", lambda: False,
            lambda: False, lambda: "live", threading.Event(),
            shared_state=shared,
        )
        from unittest.mock import MagicMock
        with patch("app.requests.Session") as session_class:
            session = MagicMock()
            session_class.return_value = session
            with patch("app.translate_with_google_fast", side_effect=lambda text, **_: "переведено") as google:
                self.assertEqual(worker._translate("hi there", "ru"), "переведено")
                self.assertEqual(worker._translate("new phrase", "ru"), "переведено")
                self.assertEqual(session_class.call_count, 1)
                self.assertEqual(google.call_count, 2)
                self.assertIs(google.call_args.kwargs["request_get"], session.get)

    def test_overlay_preserves_chat_order_despite_parallel_completions(self):
        from app import OverlayItem, OverlayWindow
        from collections import deque
        overlay = OverlayWindow.__new__(OverlayWindow)
        overlay.items = deque()
        overlay._fade_alpha = 1.0
        overlay.edit_mode = True
        overlay._cancel_fade = lambda: None
        overlay._overlay_cfg = lambda: {"fade_enabled": False, "max_messages": 4}
        overlay.render = lambda: None
        overlay._set_text_alpha = lambda _value: None
        def item(text, when):
            return OverlayItem("Player", text, text, when)
        overlay.add(item("newer", 20))
        overlay.add(item("older", 10))
        overlay.add(item("newest", 30))
        self.assertEqual([x.original for x in overlay.items],
                         ["older", "newer", "newest"])

    def test_mymemory_connection_is_reused_per_worker(self):
        worker = TranslatorWorker(
            queue.Queue(), queue.Queue(), lambda: "ru", lambda: False,
            lambda: False, lambda: "live", threading.Event(),
        )
        from unittest.mock import MagicMock
        with patch("app.requests.Session") as session_class:
            session = MagicMock()
            session_class.return_value = session
            with patch("app.translate_with_mymemory", return_value="другое") as fallback:
                self.assertEqual(worker._translate_fallback("hello", "ru"), "другое")
                self.assertEqual(worker._translate_fallback("bye", "ru"), "другое")
                session_class.assert_called_once()
                self.assertEqual(fallback.call_count, 2)
                self.assertIs(fallback.call_args.kwargs["request_get"], session.get)

    def test_second_worker_is_not_blocked_by_slow_first(self):
        # Deterministic queue/head-of-line test: the first provider is stuck
        # while the second message should reach the overlay immediately.
        shared = TranslationWorkerSharedState()
        tasks, events, stop = queue.Queue(), queue.Queue(), threading.Event()
        started_slow = threading.Event()
        release_slow = threading.Event()
        def create():
            return TranslatorWorker(
                tasks, events, lambda: "ru", lambda: False,
                lambda: False, lambda: "live", stop,
                shared_state=shared,
            )
        first, second = create(), create()
        def slow_provider(text, target):
            started_slow.set()
            release_slow.wait(timeout=2)
            return "медленный"
        def fast_provider(text, target):
            return "быстрый"
        first._translate = slow_provider
        second._translate = fast_provider
        first.start()
        tasks.put(ChatMessage("A", "hello slow message"))
        self.assertTrue(started_slow.wait(timeout=2))
        second.start()
        tasks.put(ChatMessage("B", "hello fast message"))
        try:
            received = events.get(timeout=2)
            self.assertEqual(received[0], "translation")
            self.assertEqual(received[1].nickname, "B")
            self.assertEqual(received[2], "быстрый")
        finally:
            release_slow.set()
            tasks.join()
            stop.set()
            first.join(timeout=3)
            second.join(timeout=3)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())


class LanguageDetectionSafetyTests(unittest.TestCase):
    def test_generic_cyrillic_is_not_forced_to_russian(self):
        with patch("langdetect.detect", return_value="bg") as detector:
            result = detect_source_language("добър ден")
        self.assertEqual(result, "bg")
        detector.assert_called_once()

    def test_russian_specific_letters_are_fast(self):
        self.assertEqual(detect_source_language("ты"), "ru")

    def test_ukrainian_specific_letters_are_fast(self):
        self.assertEqual(detect_source_language("привіт"), "uk")


if __name__ == "__main__":
    unittest.main()
