"""Native per-pixel-alpha subtitles for CoD2, reused from stable overlay.

The stable Win32LayeredOverlay is maintained in the repository root. This
adapter lets the experimental voice app use the same non-activating HWND and
rendering path rather than Tk Toplevel during gameplay.

No DirectX injection or process memory access. Actual exclusive-fullscreen
visibility depends on Windows, game rendering path and GPU driver.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

if os.name == "nt":
    from win32_layered_overlay import Win32LayeredOverlay
else:
    Win32LayeredOverlay = None


class VoiceNativeOverlay:
    def __init__(self, x=90, y=75):
        if Win32LayeredOverlay is None:
            raise RuntimeError("Native Windows overlay is unavailable")
        self.surface = Win32LayeredOverlay()
        self.config = {
            "x": int(x),
            "y": int(y),
            "width": 690,
            "height": 120,
            "font_size": 12,
            "background_opacity": 0.50,
            "background_only_with_messages": False,
            "auto_height": True,
            "compact_background": False,
        }
        self.text = "Ожидание входящего голоса"
        self.language = "VOICE"
        self.render()
        self.surface.show()

    def render(self):
        """Reuse native text/image renderer; title and subtitle stay legible."""
        item = SimpleNamespace(
            nickname=f"🎙 {self.language}",
            translated=self.text,
            original=self.text,
        )
        return self.surface.render([item], self.config, show_original=False)

    def update(self, language: str, original: str, translated: str = ""):
        self.language = str(language or "VOICE")
        # The HUD should show the actual translation, not a second line of
        # potentially unsupported non-Latin glyphs in square brackets.
        # Original speech remains available in the main transcript window.
        self.text = str(translated or original or "").strip()
        if not self.text:
            self.text = "Ожидание входящего голоса"
        self.render()
        self.surface.force_topmost()

    def move(self, x: int, y: int):
        self.config["x"] = int(x)
        self.config["y"] = int(y)
        self.surface.move(int(x), int(y))
        # Re-render retains position after future speech updates.
        self.render()

    def show(self):
        self.surface.show()

    def hide(self):
        self.surface.hide()

    def force_topmost(self):
        self.surface.force_topmost()

    def destroy(self):
        self.surface.destroy()
