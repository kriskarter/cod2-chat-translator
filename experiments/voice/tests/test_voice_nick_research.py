"""Speaker-research diagnostics: never infer nick from neighboring chat text."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_nick_research import (
    LogClueTail, VoiceNickResearch, redact_voice_log_line, voice_console_logs
)


class VoiceNickResearchTests(unittest.TestCase):
    def test_secret_lines_rejected(self):
        self.assertIsNone(redact_voice_log_line("Voice password=helloworld"))
        self.assertIsNone(redact_voice_log_line("Voice rcon_password something"))

    def test_ips_redacted_and_chat_not_assigned_as_speaker(self):
        self.assertEqual(
            redact_voice_log_line("Voice packets from 192.168.1.50:28960"),
            "Voice packets from <IP>",
        )
        self.assertIsNone(redact_voice_log_line("Pirat: Hello everyone!"))

    def test_voice_log_path_bounded_and_tail_starts_at_eof(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "main" / "console_mp.log"
            path.parent.mkdir()
            path.write_bytes(b"Voice older=1\n")
            self.assertIn(path.resolve(), voice_console_logs(root / "voice.wav"))
            tail = LogClueTail(root / "voice.wav")
            self.assertEqual(tail.recent_clues(), [])
            with path.open("ab") as log:
                log.write(b"Voice transmission from client 12\n")
            self.assertEqual(tail.recent_clues(), ["Voice transmission from client 12"])

    def test_jsonl_contains_unknown_not_guessed_player_and_manual_mark(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = root / "nick_voice_report.jsonl"
            probe = VoiceNickResearch(root / "voice.wav", report)
            probe.observe(seq=8, seconds=1.5, origin="live")
            self.assertTrue(probe.annotate("VooDoo"))
            lines = [json.loads(x) for x in report.read_text("utf-8").splitlines()]
            self.assertEqual(lines[0]["identity_status"], "unknown")
            self.assertNotIn("nickname", lines[0])
            self.assertEqual(lines[1]["seq"], 8)
            self.assertEqual(lines[1]["nickname"], "VooDoo")
            self.assertEqual(lines[1]["identity_status"], "user_verified_for_this_utterance_only")

    def test_screen_frame_does_not_assign_speaker_automatically(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = root / "voice_nickname_research.jsonl"
            research = VoiceNickResearch(root / "voice.wav", report)
            research.record_screen_frame(
                seq_hint=19,
                file_name="voice_speaker_20261112_111111.jpg",
                quality="ok",
            )
            entry = json.loads(report.read_text("utf-8").splitlines()[0])
            self.assertEqual(entry["identity_status"], "unknown")
            self.assertNotIn("nickname", entry)
            self.assertEqual(
                entry["voice_seq_hint_not_verified"], 19
            )
            self.assertEqual(entry["capture_quality"], "ok")

    def test_recording_mode_no_raw_voice_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "report.jsonl"
            probe = VoiceNickResearch(Path(folder) / "voice.wav", report)
            probe.observe(seq=2, seconds=2.5, origin="recording")
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
