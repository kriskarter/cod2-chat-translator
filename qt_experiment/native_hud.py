"""Qt-owned lifecycle for the existing Win32 layered HUD (no Tk windows)."""
import os
import time
from collections import deque
from app import OverlayItem


class NativeHud:
    def __init__(self, config, show_original=False, factory=None, clock=time.monotonic):
        self.config = dict(config)
        self.show_original = bool(show_original)
        self.factory = factory
        self.clock = clock
        self.items = deque(maxlen=max(1, min(10, int(config.get("max_messages", 4)))))
        self.ttl = max(1, min(120, float(config.get("message_ttl_seconds", 10))))
        self.surface = None
        self.enabled = False
        self.last_error = ""
        self._alpha = 1.0

    @property
    def available(self):
        return self.factory is not None or os.name == "nt"

    def enable(self, value):
        if not value:
            self.enabled = False
            self.items.clear()
            if self.surface:
                self.surface.hide()
            return False
        if not self.available:
            return False
        try:
            if self.surface is None:
                factory = self.factory
                if factory is None:
                    from win32_layered_overlay import Win32LayeredOverlay
                    factory = Win32LayeredOverlay
                self.surface = factory()
            self.last_error = ""
            self.enabled = True
            self._render()
            return self.enabled
        except Exception as error:
            self._fail(error)
            return False

    def _fail(self, error):
        self.last_error = str(error)
        self.close()

    def _render(self):
        if not self.enabled or self.surface is None:
            return
        try:
            if not self.items and self.config.get("background_only_with_messages", True):
                self.surface.hide()
                return
            self._alpha = 1.0
            self.surface.render(list(self.items), self.config, self.show_original, alpha=self._alpha)
            self.surface.show()
        except Exception as error:
            self._fail(error)

    def add(self, nickname, original, translated):
        if not self.enabled:
            return
        self.items.appendleft(OverlayItem(nickname, original, translated, self.clock()))
        self._render()

    def resize_buffer(self, count):
        self.items = deque(list(self.items)[:count], maxlen=count)
        self.config["max_messages"] = count
        self._render()

    def clear(self):
        self.items.clear()
        self._render()

    def tick(self):
        before = len(self.items)
        while self.items and self.clock() - self.items[-1].created_at >= self.ttl:
            self.items.pop()
        if before != len(self.items):
            self._render()
        if not self.enabled or not self.surface or not self.items:
            return
        # Fade the whole layered HUD only when the newest item approaches expiry.
        fade = max(.08, min(2.0, float(self.config.get("fade_ms", 220)) / 1000))
        remaining = self.ttl - (self.clock() - self.items[0].created_at)
        alpha = max(0., min(1., remaining / fade)) if self.config.get("fade_enabled", True) else 1.
        if abs(alpha - self._alpha) > .025:
            try:
                self.surface.set_alpha(alpha)
                self._alpha = alpha
            except Exception as error:
                self._fail(error)

    def close(self):
        self.enabled = False
        self.items.clear()
        if self.surface:
            try:
                self.surface.destroy()
            except Exception:
                pass
            self.surface = None
