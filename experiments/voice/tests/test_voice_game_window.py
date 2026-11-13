"""Platform-independent tests for Windows overlay style decisions."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_game_window import (
    WS_CAPTION,
    WS_EX_NOACTIVATE,
    WS_EX_TOOLWINDOW,
    WS_EX_TOPMOST,
    WS_EX_TRANSPARENT,
    WS_POPUP,
    WS_SYSMENU,
    WS_THICKFRAME,
    WS_VISIBLE,
    borderless_styles,
    find_cod2_window,
    is_cod2_running,
    is_cod2_foreground,
    overlay_styles,
)


class CoD2BorderlessTests(unittest.TestCase):
    def test_remove_game_borders_and_topmost_without_hiding_game(self):
        input_style = WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_VISIBLE
        style, exstyle = borderless_styles(input_style, WS_EX_TOPMOST | 0x100)
        self.assertEqual(style & (WS_CAPTION | WS_THICKFRAME | WS_SYSMENU), 0)
        self.assertTrue(style & WS_POPUP)
        self.assertTrue(style & WS_VISIBLE)
        self.assertFalse(exstyle & WS_EX_TOPMOST)
        self.assertTrue(exstyle & 0x100)

    def test_borderless_style_is_idempotent(self):
        style, exstyle = borderless_styles(WS_POPUP | WS_VISIBLE, 0)
        self.assertEqual(borderless_styles(style, exstyle), (style, exstyle))


class VoiceOverlayTests(unittest.TestCase):
    def test_windows_enumeration_does_not_require_a_running_game(self):
        # Real Win32 signature smoke-test in the Windows CI runner.
        if os.name == "nt":
            self.assertIsNone(find_cod2_window())
            self.assertFalse(is_cod2_running())
            self.assertFalse(is_cod2_foreground())

    def test_click_through_does_not_destroy_tk_layered_style(self):
        layered = 0x00080000
        ex = overlay_styles(layered, click_through=True)
        self.assertTrue(ex & layered)
        self.assertTrue(ex & WS_EX_TRANSPARENT)
        self.assertTrue(ex & WS_EX_NOACTIVATE)
        self.assertTrue(ex & WS_EX_TOOLWINDOW)

    def test_drag_mode_reenables_mouse_input(self):
        ex = overlay_styles(0x00080000, click_through=True)
        editable = overlay_styles(ex, click_through=False)
        self.assertFalse(editable & WS_EX_TRANSPARENT)
        self.assertFalse(editable & WS_EX_NOACTIVATE)
        self.assertTrue(editable & WS_EX_TOOLWINDOW)
        self.assertTrue(editable & 0x00080000)

    def test_toggle_overlay_style_is_idempotent(self):
        original = WS_EX_TOPMOST | 0x00080000
        once = overlay_styles(original, click_through=True)
        twice = overlay_styles(once, click_through=True)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
