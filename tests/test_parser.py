from pathlib import Path
import tempfile
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



if __name__ == "__main__":
    unittest.main()
