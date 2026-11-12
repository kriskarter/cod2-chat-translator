"""Opt-in speaker screenshot research: deterministic, no live desktop needed."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_screen_probe import (
    MAX_FRAMES,
    FrameThrottle,
    candidate_frame_quality,
    capture_if_game_foreground,
    save_bounded_screenshot,
)


class VoiceSpeakerFrameTests(unittest.TestCase):
    def test_black_frame_is_rejected(self):
        black = Image.new("RGB", (800, 450), (0, 0, 0))
        self.assertEqual(candidate_frame_quality(black), "dark_or_black")
        with tempfile.TemporaryDirectory() as root:
            path, reason = save_bounded_screenshot(black, Path(root), "123")
            self.assertIsNone(path)
            self.assertEqual(reason, "dark_or_black")
            self.assertFalse(list(Path(root).glob("*.jpg")))

    def test_uniform_desktop_placeholder_is_rejected(self):
        image = Image.new("RGB", (100, 100), (120, 120, 120))
        self.assertEqual(candidate_frame_quality(image), "nearly_uniform")

    def test_game_like_frame_is_kept_and_resized(self):
        image = Image.new("RGB", (2000, 1000), (10, 10, 10))
        for x in range(1000):
            for y in range(60):
                image.putpixel((x, y), (200, 180, 160))
        with tempfile.TemporaryDirectory() as root:
            path, reason = save_bounded_screenshot(image, Path(root), "2026_11_12_111")
            self.assertEqual(reason, "ok")
            self.assertTrue(path.is_file())
            with Image.open(path) as saved:
                self.assertLessEqual(saved.width, 1600)
                self.assertEqual(saved.size, (1600, 800))

    def test_evidence_frames_bounded_to_twelve(self):
        image = Image.new("RGB", (200, 100), (2, 2, 2))
        for x in range(100):
            for y in range(35):
                image.putpixel((x, y), (220, 200, 170))
        with tempfile.TemporaryDirectory() as root:
            for i in range(MAX_FRAMES + 4):
                path, _ = save_bounded_screenshot(
                    image, Path(root), f"frame_{i:04}"
                )
                self.assertIsNotNone(path)
            self.assertEqual(len(list(Path(root).glob("*.jpg"))), MAX_FRAMES)

    def test_capture_cannot_snapshot_desktop_if_cod2_not_foreground(self):
        # On non-Windows no screenshot, Windows also refuses if game not focused.
        with tempfile.TemporaryDirectory() as root:
            status, path = capture_if_game_foreground(
                Path(root), "2026_11", lambda: False
            )
            self.assertIn(status, {"windows_only", "game_not_foreground"})
            self.assertIsNone(path)
            self.assertFalse(list(Path(root).glob("*.jpg")))

    def test_throttle_drops_dense_voice_bursts(self):
        throttle = FrameThrottle(min_interval=2)
        self.assertTrue(throttle.allow(10))
        self.assertFalse(throttle.allow(11.9))
        self.assertTrue(throttle.allow(12))
        self.assertFalse(throttle.allow(13))


if __name__ == "__main__":
    unittest.main()
