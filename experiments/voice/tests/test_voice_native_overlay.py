"""Native voice surface adapter: no Windows desktop needed for these tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_native_overlay import VoiceNativeOverlay


class FakeSurface:
    def __init__(self):
        self.render_calls = []
        self.move_calls = []
        self.shown = 0
        self.hidden = 0
        self.raised = 0
        self.destroyed = 0

    def render(self, items, config, show_original, alpha=1.0):
        self.render_calls.append((items, dict(config), show_original, alpha))
        return (120, 690, 120)

    def move(self, x, y):
        self.move_calls.append((x, y))

    def show(self):
        self.shown += 1

    def hide(self):
        self.hidden += 1

    def force_topmost(self):
        self.raised += 1

    def destroy(self):
        self.destroyed += 1


class VoiceNativeOverlayTests(unittest.TestCase):
    def test_localized_subtitle_uses_native_renderer(self):
        with patch("voice_native_overlay.Win32LayeredOverlay", FakeSurface):
            surface = VoiceNativeOverlay(90, 75)
            surface.update("PL", "idę na B", "Иду на B")
        last = surface.surface.render_calls[-1]
        self.assertEqual(last[0][0].nickname, "ГОЛОС · PL")
        self.assertIn("Иду на B", last[0][0].translated)
        self.assertEqual(last[1]["x"], 90)
        self.assertEqual(last[1]["y"], 75)
        self.assertFalse(last[2])

    def test_moving_preview_updates_future_native_render(self):
        with patch("voice_native_overlay.Win32LayeredOverlay", FakeSurface):
            surface = VoiceNativeOverlay(90, 75)
            surface.move(450, 220)
            surface.update("EN", "Left side")
        self.assertEqual(surface.surface.move_calls, [(450, 220)])
        self.assertEqual(surface.surface.render_calls[-1][1]["x"], 450)
        self.assertEqual(surface.surface.render_calls[-1][1]["y"], 220)

    def test_visibility_and_destroy(self):
        with patch("voice_native_overlay.Win32LayeredOverlay", FakeSurface):
            surface = VoiceNativeOverlay()
            surface.hide()
            surface.show()
            surface.force_topmost()
            surface.destroy()
        self.assertEqual(surface.surface.shown, 2)
        self.assertEqual(surface.surface.hidden, 1)
        self.assertEqual(surface.surface.raised, 1)
        self.assertEqual(surface.surface.destroyed, 1)


if __name__ == "__main__":
    unittest.main()
