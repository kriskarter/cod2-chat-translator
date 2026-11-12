"""Read CoD2's append-only incoming voice stream without touching the game.

Input is headerless little-endian PCM, mono, signed 16-bit, 8,000 Hz.
The engine has no network / ASR dependencies and can be unit-tested alone.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SAMPLE_RATE = 8000
SAMPLE_WIDTH = 2
BYTE_RATE = SAMPLE_RATE * SAMPLE_WIDTH


@dataclass(frozen=True)
class AudioJob:
    seq: int
    raw_pcm: bytes
    origin: str
    queued_at: float = field(default_factory=time.monotonic)
    speaker_slot: int | None = None
    speaker_label: str = "Игрок (ник неизвестен)"
    speaker_evidence: str = "not_checked"


class FileTail:
    """Only yield newly appended, complete PCM samples.

    On startup it skips existing audio so old speech isn't retranslated.
    If CoD2 truncates or rotates the file, it starts at byte 0 of the new
    file. No file locks, modifications, or game hooks.
    """

    def __init__(self, path: str | Path, *, from_start: bool = False):
        self.path = Path(path)
        self.from_start = from_start
        self.offset: int | None = None
        self.identity: tuple[int, int] | None = None
        # Capture the current EOF immediately, not on the first timer tick.
        try:
            stat = self.path.stat()
            self.identity = (stat.st_dev, stat.st_ino)
            self.offset = 0 if from_start else stat.st_size - stat.st_size % SAMPLE_WIDTH
        except (FileNotFoundError, PermissionError, OSError):
            # If voice.wav is created after Start, its first utterance matters.
            pass

    def read_new(self, limit: int = BYTE_RATE * 15) -> bytes:
        try:
            stat = self.path.stat()
        except (FileNotFoundError, PermissionError, OSError):
            return b""

        identity = (stat.st_dev, stat.st_ino)
        reset = (
            self.offset is None
            or self.identity != identity
            or stat.st_size < self.offset
        )
        if reset:
            # Creation, truncation and rotation all start from byte zero.
            # Existing old audio was skipped in __init__ instead.
            self.offset = 0
            self.identity = identity

        available = max(0, stat.st_size - self.offset)
        count = min(available - available % SAMPLE_WIDTH, limit - limit % SAMPLE_WIDTH)
        if count <= 0:
            return b""

        try:
            with self.path.open("rb") as stream:
                stream.seek(self.offset)
                data = stream.read(count)
        except (PermissionError, OSError):
            return b""

        data = data[:len(data) // SAMPLE_WIDTH * SAMPLE_WIDTH]
        self.offset += len(data)
        return data


class LiveCollector:
    """Aggregate appended audio until the file stops growing.

    CoD2 often stops writing when push-to-talk ends without appending
    silence. Wall-clock inactivity, not only audio energy, is therefore
    the primary utterance boundary in live mode.
    """

    def __init__(self, *, idle_seconds: float = 0.85, max_seconds: float = 11):
        self.idle_seconds = idle_seconds
        self.max_bytes = int(max_seconds * BYTE_RATE)
        self.buffer = bytearray()
        self.last_growth: float | None = None

    def reset(self) -> None:
        self.buffer.clear()
        self.last_growth = None

    def feed(self, data: bytes, now: float | None = None) -> list[bytes]:
        if not data:
            return []
        if len(data) % 2:
            raise ValueError("Unaligned PCM data")
        if now is None:
            now = time.monotonic()
        self.last_growth = now
        self.buffer.extend(data)
        ready = []
        while len(self.buffer) >= self.max_bytes:
            ready.append(bytes(self.buffer[:self.max_bytes]))
            del self.buffer[:self.max_bytes]
        return ready

    def flush_if_idle(self, now: float | None = None) -> bytes | None:
        if now is None:
            now = time.monotonic()
        if (
            self.buffer
            and self.last_growth is not None
            and now - self.last_growth >= self.idle_seconds
        ):
            result = bytes(self.buffer)
            self.reset()
            return result
        return None


def split_utterances(
    raw_pcm: bytes,
    *,
    min_speech_seconds: float = 0.28,
    silence_seconds: float = 0.62,
    pad_seconds: float = 0.15,
    max_seconds: float = 12.0,
) -> list[bytes]:
    """RMS gate for coarse speech splitting (not speech recognition).

    Very faint speech and simultaneous talkers can be missed or joined.
    Short-frame gating is deliberately kept simple for fast offline tests.
    """
    if not raw_pcm or len(raw_pcm) % 2:
        return []

    frame_size = 160  # 20 ms at 8 kHz
    samples = np.frombuffer(raw_pcm, dtype="<i2")
    frame_count = len(samples) // frame_size
    if frame_count < int(min_speech_seconds / .02):
        return []

    windows = samples[:frame_count * frame_size].reshape(frame_count, frame_size)
    rms = np.sqrt(np.mean(windows.astype(np.float32) ** 2, axis=1))
    # A low baseline accommodates the large quiet gaps seen in voice.wav.
    noise = float(np.percentile(rms, 20))
    threshold = max(105.0, min(450.0, noise * 2.5))
    voiced = np.flatnonzero(rms >= threshold)
    if voiced.size == 0:
        return []

    max_gap = max(1, round(silence_seconds / .02))
    speech_min_frames = max(1, round(min_speech_seconds / .02))
    pad = max(0, round(pad_seconds / .02))
    max_frames = max(1, round(max_seconds / .02))

    clusters: list[tuple[int, int, int]] = []
    first = last = int(voiced[0])
    active_frames = 1
    for position in voiced[1:]:
        position = int(position)
        if position - last > max_gap:
            clusters.append((first, last + 1, active_frames))
            first = position
            active_frames = 0
        last = position
        active_frames += 1
    clusters.append((first, last + 1, active_frames))

    output = []
    prev_end = 0
    for first, end, active in clusters:
        if active < speech_min_frames:
            continue
        start = max(prev_end, first - pad)
        stop = min(frame_count, end + pad)
        while stop > start:
            cut = min(stop, start + max_frames)
            block = samples[start * frame_size:cut * frame_size].tobytes()
            if len(block) >= int(min_speech_seconds * BYTE_RATE):
                output.append(block)
            start = cut
        prev_end = stop
    return output


def to_whisper_audio(raw_pcm: bytes) -> np.ndarray:
    """Linear 8 -> 16 kHz resampling, float32 normalized as Whisper expects."""
    if len(raw_pcm) % 2:
        raise ValueError("Odd number of PCM bytes")
    source = np.frombuffer(raw_pcm, dtype="<i2").astype(np.float32) / 32768.0
    if not len(source):
        return np.empty(0, dtype=np.float32)
    result = np.interp(
        np.arange(len(source) * 2, dtype=np.float32) / 2.0,
        np.arange(len(source), dtype=np.float32),
        source,
    )
    return result.astype(np.float32, copy=False)


def guess_voice_path() -> Path:
    """Prefer the demonstrated game directory, then common Steam locations."""
    candidates = [
        Path(r"D:\SteamLibrary\steamapps\common\Call of Duty 2\voice.wav"),
        Path(r"C:\Program Files (x86)\Steam\steamapps\common\Call of Duty 2\voice.wav"),
        Path(r"C:\Program Files\Steam\steamapps\common\Call of Duty 2\voice.wav"),
    ]
    return next((path for path in candidates if path.exists()), candidates[0])
