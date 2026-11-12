"""Opt-in Windows game-frame evidence for future CoD2 speaker nickname OCR.

No screen images are taken unless the user explicitly enables the checkbox.
Capture runs in a separate worker, never blocking the voice file tail. The
frames are local-only, bounded, and not treated as verified speaker identities.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from time import monotonic

from PIL import Image, ImageGrab

MAX_FRAMES = 12
MAX_WIDTH = 1600


def candidate_frame_quality(image: Image.Image) -> str:
    """Detect obvious black/blank frames typical of exclusive game rendering."""
    sample = image.convert("RGB").resize((48, 27))
    pixels = list(sample.get_flattened_data())
    if not pixels:
        return "empty"
    bright = sum(max(r, g, b) > 35 for r, g, b in pixels)
    lo = tuple(min(v[i] for v in pixels) for i in range(3))
    hi = tuple(max(v[i] for v in pixels) for i in range(3))
    if bright < len(pixels) * 0.035:
        return "dark_or_black"
    if all(hi[i] - lo[i] < 10 for i in range(3)):
        return "nearly_uniform"
    return "ok"


def save_bounded_screenshot(image: Image.Image, folder: Path, label: str) -> tuple[Path | None, str]:
    """Keep only a bounded set of local screenshots to avoid disk growth."""
    quality = candidate_frame_quality(image)
    if quality != "ok":
        return None, quality
    folder.mkdir(parents=True, exist_ok=True)
    # Screen captures can include private text. Never expose automatically.
    # Keep original aspect ratio; 1600 px gives useful small HUD text.
    if image.width > MAX_WIDTH:
        height = round(image.height * (MAX_WIDTH / image.width))
        image = image.resize((MAX_WIDTH, max(1, height)), Image.Resampling.LANCZOS)
    filename = "voice_speaker_" + "".join(c for c in label if c.isdigit() or c == "_")[:32] + ".jpg"
    path = folder / filename
    image.convert("RGB").save(path, "JPEG", quality=78, optimize=True)
    recent = sorted(folder.glob("voice_speaker_*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    for obsolete in recent[MAX_FRAMES:]:
        obsolete.unlink(missing_ok=True)
    return path, quality


def capture_if_game_foreground(folder: Path, label: str, is_game_foreground) -> tuple[str, Path | None]:
    """Check foreground BEFORE invoking costly image capture."""
    if os.name != "nt":
        return "windows_only", None
    if not is_game_foreground():
        return "game_not_foreground", None
    try:
        frame = ImageGrab.grab()
        path, quality = save_bounded_screenshot(frame, folder, label)
        return quality, path
    except Exception as exc:
        return "capture_error:" + type(exc).__name__, None


class FrameThrottle:
    """No more than one screenshot per ~2 seconds, even during rapid speech."""
    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._last = float("-inf")

    def allow(self, now: float | None = None) -> bool:
        if now is None:
            now = monotonic()
        with self._lock:
            if now - self._last < self.min_interval:
                return False
            self._last = now
            return True
