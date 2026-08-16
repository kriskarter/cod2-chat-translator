from pathlib import Path
import tempfile
import threading
import time
import unittest

from app import (
    ChatMessage,
    compact_background_size,
    default_overlay_position,
    RecentDuplicateFilter,
    gaming_slang_transform,
    is_map_change_line,
    looks_like_target_language,
    normalize_for_compare,
    parse_chat_line,
    read_log_messages,
    infer_cod2_root,
    default_profile_name,
    apply_primary_profile_name,
    merge_server_profiles,
    discover_cod2_logs,
    activity_snapshot,
    choose_active_log_from_activity,
    LogTailer,
    TranslatorWorker,
    TranslationServiceTemporaryError,
    looks_like_translation_service_error,
)


class ParserTests(unittest.TestCase):
    def test_basic_english_chat(self):
        msg = parse_chat_line("One_ShOt_ONe_Kill^7: ^7i bashed you xd")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.nickname, "One_ShOt_ONe_Kill")
        self.assertEqual(msg.text, "i bashed you xd")

    def test_nickname_with_colon(self):
        msg = parse_chat_line("BeethoveN:*|PC^7: ^7Здесь все чисто.")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.nickname, "BeethoveN:*|PC")
        self.assertEqual(msg.text, "Здесь все чисто.")

    def test_dead_prefix(self):
        msg = parse_chat_line("(Погиб)Adajet^7: ^7ups")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.nickname, "(Погиб)Adajet")
        self.assertEqual(msg.text, "ups")

    def test_service_line_ignored(self):
        self.assertIsNone(parse_chat_line("Writing logininfo.cfg."))
        self.assertIsNone(parse_chat_line("No tag_flash in CG_CalcMuzzlePoint on entity 25."))

    def test_admin_chat(self):
        msg = parse_chat_line("[OBRN] TA^5RS^7 (admin): ^7Got a map idea? Share it with us")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.nickname, "[OBRN] TARS (admin)")
        self.assertEqual(msg.text, "Got a map idea? Share it with us")

    def test_map_load_noise_and_secrets_ignored(self):
        self.assertIsNone(parse_chat_line("ERROR: Couldn't find material 'loadscreen_silotown'"))
        self.assertIsNone(parse_chat_line("      dvar set ui_pwlogin example-secret"))
        self.assertIsNone(parse_chat_line("      dvar set com_errorMessage ^3Warning! ^7Reconnect"))

    def test_cp1251_log(self):
        raw = (
            "logfile opened\r\n"
            "BeethoveN:*|PC^7: ^7Здесь все чисто.\r\n"
            "Adajet^7: ^7hard night\r\n"
        ).encode("cp1251")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "console_mp.log"
            path.write_bytes(raw)
            messages = read_log_messages(path)
        self.assertEqual([(m.nickname, m.text) for m in messages], [
            ("BeethoveN:*|PC", "Здесь все чисто."),
            ("Adajet", "hard night"),
        ])

    def test_same_language_ru_obvious(self):
        self.assertTrue(looks_like_target_language("дима привет", "ru"))
        self.assertTrue(looks_like_target_language("Здесь все чисто.", "ru"))
        self.assertFalse(looks_like_target_language("привіт друже", "ru"))
        self.assertFalse(looks_like_target_language("hello there", "ru"))

    def test_normalize_for_compare(self):
        self.assertEqual(normalize_for_compare("  Hello   WORLD "), "hello world")

    def test_gg_is_gaming_slang_for_russian(self):
        prepared, direct = gaming_slang_transform("gg", "ru")
        self.assertEqual(prepared, "gg")
        self.assertEqual(direct, "хорошая игра")

    def test_russian_gg_to_english(self):
        prepared, direct = gaming_slang_transform("гг", "en")
        self.assertEqual(direct, "good game")

    def test_slang_expands_for_third_language(self):
        prepared, direct = gaming_slang_transform("ns!", "pl")
        self.assertEqual(prepared, "nice shot!")
        self.assertIsNone(direct)


    def test_gg_punctuation_is_preserved(self):
        prepared, direct = gaming_slang_transform("gg!", "ru")
        self.assertEqual(prepared, "gg!")
        self.assertEqual(direct, "хорошая игра!")

    def test_inline_slang_is_expanded(self):
        prepared, direct = gaming_slang_transform("gg bro", "pl")
        self.assertEqual(prepared, "good game bro")
        self.assertIsNone(direct)

    def test_fps_slang_headshot(self):
        prepared, direct = gaming_slang_transform("hs", "ru")
        self.assertEqual(direct, "выстрел в голову")

    def test_russian_inline_slang_to_other_language(self):
        prepared, direct = gaming_slang_transform("спс всем", "de")
        self.assertEqual(prepared, "спасибо всем")
        self.assertIsNone(direct)

    def test_map_change_detection(self):
        self.assertTrue(is_map_change_line("Server changing map silotown, gametype dm"))
        self.assertFalse(is_map_change_line("Player^7: ^7Server changing map maybe"))

    def test_duplicate_filter(self):
        f = RecentDuplicateFilter(window_seconds=4)
        msg = ChatMessage("Rose", "gg")
        self.assertFalse(f.is_duplicate(msg, now=10.0))
        self.assertTrue(f.is_duplicate(msg, now=12.0))
        self.assertFalse(f.is_duplicate(msg, now=20.0))
        self.assertFalse(f.is_duplicate(ChatMessage("Other", "gg"), now=20.5))

    def test_cod2_extended_slang(self):
        cases = {
            "rush b": "быстрая атака на B",
            "behind you": "враг сзади",
            "arty": "артиллерия",
            "ks": "серия убийств",
            "votekick": "голосование за кик",
            "tdm": "командный бой",
        }
        for source, expected in cases.items():
            _prepared, direct = gaming_slang_transform(source, "ru")
            self.assertEqual(direct, expected, source)

    def test_extended_slang_inline_for_third_language(self):
        prepared, direct = gaming_slang_transform("rush b pls", "de")
        self.assertIn("rush attack toward B", prepared)
        self.assertIn("please", prepared)
        self.assertIsNone(direct)


    def test_default_overlay_position_scales_with_screen(self):
        x1, y1 = default_overlay_position(1366, 768, 500, 150)
        x2, y2 = default_overlay_position(1920, 1080, 500, 150)
        self.assertLessEqual(x1, 12)
        self.assertGreater(y1, 300)
        self.assertLess(y1, 400)
        self.assertGreater(y2, y1)

    def test_live_slang_style_is_colloquial(self):
        _prepared, direct = gaming_slang_transform("wtf", "ru", "live")
        self.assertEqual(direct, "какого хрена")
        _prepared, direct = gaming_slang_transform("owned", "ru", "live")
        self.assertEqual(direct, "размотал")

    def test_raw_slang_style_preserves_profanity(self):
        _prepared, direct = gaming_slang_transform("wtf", "ru", "raw")
        self.assertEqual(direct, "что за хуйня")
        _prepared, direct = gaming_slang_transform("fu", "ru", "raw")
        self.assertEqual(direct, "пошёл нахуй")

    def test_clear_slang_style_stays_explanatory(self):
        _prepared, direct = gaming_slang_transform("wtf", "ru", "clear")
        self.assertEqual(direct, "что за фигня")
        _prepared, direct = gaming_slang_transform("noob", "ru", "clear")
        self.assertEqual(direct, "неопытный игрок")

    def test_compact_background_size(self):
        self.assertEqual(compact_background_size(180, 42, 500, 150), (188, 45))
        self.assertEqual(compact_background_size(900, 300, 500, 150), (500, 150))
        self.assertEqual(compact_background_size(10, 5, 500, 150), (70, 28))

    def test_camp_phrase_is_not_translated_as_tourist_camp(self):
        prepared, direct = gaming_slang_transform("stop camp idiot", "ru", "live")
        self.assertEqual(prepared, "stop camp idiot")
        self.assertEqual(direct, "хватит кемперить, идиот")

        _prepared, direct = gaming_slang_transform("stop camping!", "ru", "raw")
        self.assertEqual(direct, "хватит крысить!")

        prepared, direct = gaming_slang_transform("please stop camping bro", "de", "live")
        self.assertIn("stop staying in one position waiting for enemies", prepared.lower())
        self.assertIsNone(direct)


    def test_server_profile_root_and_default_name(self):
        log = Path(r"D:/SteamLibrary/steamapps/common/Call of Duty 2/oboronay3/console_mp.log")
        self.assertEqual(infer_cod2_root(log).name, "Call of Duty 2")
        self.assertEqual(default_profile_name(log), "oboronay3")
        self.assertEqual(default_profile_name(log.parent.parent / "main" / "console_mp.log"), "Vanilla (main)")

    def test_primary_profile_uses_generic_name(self):
        log = Path(r"D:/SteamLibrary/steamapps/common/Call of Duty 2/oboronay3/console_mp.log")
        profiles = merge_server_profiles([], [log])
        profiles = apply_primary_profile_name(profiles, log)
        self.assertEqual(profiles[0]["name"], "Call of Duty 2")

    def test_primary_profile_does_not_overwrite_user_rename(self):
        log = Path(r"D:/SteamLibrary/steamapps/common/Call of Duty 2/oboronay3/console_mp.log")
        profiles = [{"name": "My server", "path": str(log)}]
        profiles = apply_primary_profile_name(profiles, log)
        self.assertEqual(profiles[0]["name"], "My server")

    def test_primary_name_leaves_other_profiles_unchanged(self):
        base = Path(r"D:/SteamLibrary/steamapps/common/Call of Duty 2/oboronay3/console_mp.log")
        other = Path(r"D:/SteamLibrary/steamapps/common/Call of Duty 2/vetdm/console_mp.log")
        profiles = merge_server_profiles([], [base, other])
        profiles = apply_primary_profile_name(profiles, base)
        names = {Path(rec["path"]).parent.name: rec["name"] for rec in profiles}
        self.assertEqual(names["oboronay3"], "Call of Duty 2")
        self.assertEqual(names["vetdm"], "vetdm")

    def test_merge_profiles_preserves_user_name(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td) / "Call of Duty 2"
            old_log = game / "oboronay3" / "console_mp.log"
            new_log = game / "vetdm" / "console_mp.log"
            old_log.parent.mkdir(parents=True)
            new_log.parent.mkdir(parents=True)
            old_log.write_text("", encoding="utf-8")
            new_log.write_text("", encoding="utf-8")
            profiles = merge_server_profiles([{"name": "OBRONA", "path": str(old_log)}], [old_log, new_log])
            by_path = {Path(x["path"]).name + ":" + Path(x["path"]).parent.name: x["name"] for x in profiles}
            self.assertEqual(by_path["console_mp.log:oboronay3"], "OBRONA")
            self.assertEqual(by_path["console_mp.log:vetdm"], "vetdm")

    def test_rescan_finds_new_mod_log(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td) / "Call of Duty 2"
            main_log = game / "main" / "console_mp.log"
            main_log.parent.mkdir(parents=True)
            main_log.write_text("", encoding="utf-8")
            first = discover_cod2_logs([game])
            self.assertIn(main_log.resolve(), first)

            mod_log = game / "new_mod" / "console_mp.log"
            mod_log.parent.mkdir(parents=True)
            mod_log.write_text("", encoding="utf-8")
            second = discover_cod2_logs([game])
            self.assertIn(mod_log.resolve(), second)

    def test_activity_switches_to_log_that_started_updating(self):
        with tempfile.TemporaryDirectory() as td:
            game = Path(td) / "Call of Duty 2"
            a = game / "oboronay3" / "console_mp.log"
            b = game / "vetdm" / "console_mp.log"
            a.parent.mkdir(parents=True)
            b.parent.mkdir(parents=True)
            a.write_text("old", encoding="utf-8")
            b.write_text("old", encoding="utf-8")
            previous = activity_snapshot([a, b])
            # Make b observably different without relying on filesystem timestamp resolution.
            b.write_text("new activity on server", encoding="utf-8")
            chosen, current = choose_active_log_from_activity([a, b], previous, a, now=10_000_000_000)
            self.assertEqual(chosen, b)
            self.assertNotEqual(previous, current)

    def test_log_tailer_auto_switch_reads_triggering_chat_line(self):
        with tempfile.TemporaryDirectory() as td:
            old_log = Path(td) / "old" / "console_mp.log"
            new_log = Path(td) / "new" / "console_mp.log"
            old_log.parent.mkdir(parents=True)
            new_log.parent.mkdir(parents=True)
            old_log.write_bytes(b"boot\n")
            new_log.write_bytes(b"boot\n")

            active = {"path": old_log}
            hints: dict[str, int] = {}
            messages = []
            received = threading.Event()
            stop = threading.Event()

            def on_message(msg):
                messages.append(msg)
                received.set()

            def switch_hint(path):
                return hints.pop(str(path.resolve()), None)

            tailer = LogTailer(
                path_getter=lambda: active["path"],
                on_message=on_message,
                on_status=lambda _s: None,
                stop_event=stop,
                switch_position_getter=switch_hint,
                poll_seconds=0.01,
            )
            tailer.start()
            time.sleep(0.05)

            previous_size = new_log.stat().st_size
            with new_log.open("ab") as fh:
                fh.write(b"VooDoo^7: ^7hi all\n")
            hints[str(new_log.resolve())] = previous_size
            active["path"] = new_log

            self.assertTrue(received.wait(1.0), "auto-switch chat line was skipped")
            stop.set()
            tailer.join(timeout=1.0)
            self.assertEqual([(m.nickname, m.text) for m in messages], [("VooDoo", "hi all")])

    def test_log_tailer_manual_first_watch_does_not_replay_old_chat(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "console_mp.log"
            log.write_bytes(b"OldPlayer^7: ^7old message\n")
            messages = []
            stop = threading.Event()
            tailer = LogTailer(
                path_getter=lambda: log,
                on_message=messages.append,
                on_status=lambda _s: None,
                stop_event=stop,
                poll_seconds=0.01,
            )
            tailer.start()
            time.sleep(0.05)
            with log.open("ab") as fh:
                fh.write(b"NewPlayer^7: ^7new message\n")
            deadline = time.time() + 1.0
            while len(messages) < 1 and time.time() < deadline:
                time.sleep(0.01)
            stop.set()
            tailer.join(timeout=1.0)
            self.assertEqual([(m.nickname, m.text) for m in messages], [("NewPlayer", "new message")])


    def test_translation_error_page_is_not_treated_as_translation(self):
        error_page = "Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know."
        self.assertTrue(looks_like_translation_service_error(error_page))
        self.assertTrue(looks_like_translation_service_error("<!DOCTYPE html><html><body>oops</body></html>"))
        self.assertFalse(looks_like_translation_service_error("server error on our match?"))
        self.assertFalse(looks_like_translation_service_error("ошибка сервера"))

    def test_translator_retries_after_upstream_500_page(self):
        worker = TranslatorWorker(
            jobs=__import__("queue").Queue(),
            ui_queue=__import__("queue").Queue(),
            target_getter=lambda: "ru",
            hide_same_getter=lambda: False,
            slang_enabled_getter=lambda: False,
            slang_style_getter=lambda: "live",
            stop_event=threading.Event(),
        )

        class FakeTranslator:
            def __init__(self, responses):
                self.responses = list(responses)
            def translate(self, text):
                value = self.responses.pop(0)
                if isinstance(value, Exception):
                    raise value
                return value

        created = []
        responses = [
            "Error 500 (Server Error)!!1500.That's an error.There was an error. Please try again later.That's all we know.",
            "да",
        ]
        def factory(_target):
            fake = FakeTranslator([responses.pop(0)])
            created.append(fake)
            return fake

        worker._new_translator = factory
        original_sleep = time.sleep
        try:
            time.sleep = lambda _seconds: None
            self.assertEqual(worker._translate("yes", "ru"), "да")
        finally:
            time.sleep = original_sleep
        self.assertEqual(len(created), 2)
        self.assertEqual(worker.cache[("ru", "yes")], "да")

    def test_translator_never_caches_repeated_upstream_error_page(self):
        worker = TranslatorWorker(
            jobs=__import__("queue").Queue(),
            ui_queue=__import__("queue").Queue(),
            target_getter=lambda: "ru",
            hide_same_getter=lambda: False,
            slang_enabled_getter=lambda: False,
            slang_style_getter=lambda: "live",
            stop_event=threading.Event(),
        )

        class AlwaysBroken:
            def translate(self, text):
                return "Error 500 (Server Error). That's an error. Please try again later."

        worker._new_translator = lambda _target: AlwaysBroken()
        original_sleep = time.sleep
        try:
            time.sleep = lambda _seconds: None
            with self.assertRaises(TranslationServiceTemporaryError):
                worker._translate("hello", "ru")
        finally:
            time.sleep = original_sleep
        self.assertNotIn(("ru", "hello"), worker.cache)


if __name__ == "__main__":
    unittest.main()
