"""CoD2 voice capture configuration: use temporary game directories only."""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_capture_setup import (
    find_configs,
    patch_config,
    read_dvar,
    ensure_voice_capture,
)


class CaptureBootstrapTests(unittest.TestCase):
    def test_preserves_other_settings_and_non_utf8_user_nickname(self):
        source = (
            b'seta name "^1VooDoo\xff"\r\n'
            b'bind F9 "say test"\r\n'
            b'seta winvoice_save_voice "0"\r\n'
            b'seta r_fullscreen "1"\r\n'
        )
        out = patch_config(source, {"winvoice_save_voice": 1})
        self.assertEqual(read_dvar(out, "winvoice_save_voice"), 1)
        self.assertIn(b'bind F9 "say test"', out)
        self.assertIn(b'VooDoo\xff', out)
        self.assertIn(b'seta r_fullscreen "1"', out)
        self.assertEqual(out.count(b"\r\n"), 4)

    def test_appends_command_when_absent_without_duplicate_on_second_pass(self):
        src = b'seta name "test"'
        out = patch_config(src, {"winvoice_save_voice": 1})
        self.assertIn(b'seta winvoice_save_voice "1"', out)
        self.assertEqual(patch_config(out, {"winvoice_save_voice": 1}), out)

    def test_turns_on_both_voice_and_optional_local_console_log(self):
        src = b'seta winvoice_save_voice "0"\nseta logfile "0"\n'
        out = patch_config(src, {"winvoice_save_voice": 1, "logfile": 2})
        self.assertEqual(read_dvar(out, "winvoice_save_voice"), 1)
        self.assertEqual(read_dvar(out, "logfile"), 2)

    def test_does_not_allow_other_settings(self):
        with self.assertRaises(ValueError):
            patch_config(b'seta r_fullscreen "1"', {"r_fullscreen": 0})

    def test_backs_up_once_and_does_not_write_during_game(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            cfg = base / "main" / "players" / "VooDoo" / "config_mp.cfg"
            cfg.parent.mkdir(parents=True)
            original = b'seta winvoice_save_voice "0"\nseta name "test"\n'
            cfg.write_bytes(original)
            path = base / "voice.wav"
            self.assertIn(cfg.resolve(), find_configs(path))

            deferred = ensure_voice_capture(path, game_running=True)
            self.assertEqual(deferred.deferred, 1)
            self.assertEqual(cfg.read_bytes(), original)
            self.assertFalse(cfg.with_name("config_mp.cfg.cod2voice.bak").exists())

            applied = ensure_voice_capture(path, game_running=False)
            self.assertTrue(applied.ok)
            self.assertEqual(applied.changed, 1)
            backup = cfg.with_name("config_mp.cfg.cod2voice.bak")
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(read_dvar(cfg.read_bytes(), "winvoice_save_voice"), 1)

            again = ensure_voice_capture(path, game_running=False)
            self.assertTrue(again.ok)
            self.assertEqual(again.changed, 0)
            self.assertEqual(backup.read_bytes(), original)

    def test_scans_mod_profiles_without_writing_unrelated_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            locations = (
                root / "main" / "players" / "VooDoo" / "config_mp.cfg",
                root / "just_server" / "players" / "VooDoo" / "config_mp.cfg",
            )
            for cfg in locations:
                cfg.parent.mkdir(parents=True, exist_ok=True)
                cfg.write_bytes(b'seta winvoice_save_voice "0"')
            summary = ensure_voice_capture(root / "voice.wav", game_running=False)
            self.assertEqual(summary.found, 2)
            self.assertEqual(summary.ready, 2)
            self.assertTrue(summary.ok)
            for cfg in locations:
                self.assertEqual(read_dvar(cfg.read_bytes(), "winvoice_save_voice"), 1)

    def test_no_profile_found_does_not_create_synthetic_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            summary = ensure_voice_capture(root / "voice.wav", game_running=False)
            self.assertEqual(summary.found, 0)
            self.assertFalse(summary.ok)
            self.assertFalse((root / "main").exists())


if __name__ == "__main__":
    unittest.main()
