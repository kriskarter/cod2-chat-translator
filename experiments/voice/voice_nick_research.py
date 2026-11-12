"""Opt-in, bounded evidence capture for CoD2 voice speaker identification.

voice.wav stores decoded speech only; it contains no talker ID. A separate
console_mp.log may contain game/mod messages, but a chat nickname near a voice
event is NOT evidence that the nick spoke. We record time-correlated *hints*
without assigning an identity. Raw voice and complete console logs are never
copied into this diagnostic file.
"""
from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

_RELEVANT = re.compile(
    r"(?:\bvoice\b|\btalk(?:er|ing)?\b|говор(?:и|ит|ящий)|\bmicrophone\b)",
    re.IGNORECASE,
)
_SECRET = re.compile(
    r"(?i)(?:rconpassword|rcon_password|password|passwd|apikey|api_key|token|auth)"
)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?\b")
_MAX_LOG_BYTES = 16 * 1024
_MAX_LINES = 8


def redact_voice_log_line(text: str) -> str | None:
    """Only keep clues to voice/talker; reject secrets and mask IP addresses."""
    if _SECRET.search(text) or not _RELEVANT.search(text):
        return None
    clean = "".join(c if c >= " " else " " for c in text)[:220].strip()
    if not clean:
        return None
    return _IPV4.sub("<IP>", clean)


def voice_console_logs(voice_path: str | Path) -> list[Path]:
    root = Path(voice_path).expanduser().resolve(strict=False).parent
    candidates = [root / "console_mp.log", root / "main" / "console_mp.log"]
    try:
        candidates += list(root.glob("*/console_mp.log"))[:30]
        candidates += list(root.glob("mods/*/console_mp.log"))[:30]
    except OSError:
        pass
    unique = {os.path.normcase(str(x)): x for x in candidates if x.is_file()}
    try:
        return sorted(unique.values(), key=lambda x: x.stat().st_mtime, reverse=True)[:8]
    except OSError:
        return list(unique.values())[:8]


class LogClueTail:
    """Start from EOF, only process newly appended log text; no backfill."""
    def __init__(self, voice_path: str | Path):
        self.paths = {p: p.stat().st_size for p in voice_console_logs(voice_path)}
        self.voice_path = voice_path
        self.history: list[tuple[float, str]] = []

    def poll(self) -> None:
        for path in voice_console_logs(self.voice_path):
            try:
                size = path.stat().st_size
                offset = self.paths.get(path, size if path not in self.paths else 0)
                if size < offset:
                    offset = 0
                # Skip huge new chunks rather than holding log data in RAM.
                read_from = max(offset, size - _MAX_LOG_BYTES)
                self.paths[path] = size
                if read_from >= size:
                    continue
                with path.open("rb") as f:
                    f.seek(read_from)
                    payload = f.read(_MAX_LOG_BYTES)
                text = payload.decode("latin-1", errors="replace")
                for line in text.splitlines()[-80:]:
                    sanitized = redact_voice_log_line(line)
                    if sanitized:
                        self.history.append((monotonic(), sanitized))
            except (OSError, PermissionError, ValueError):
                continue
        now = monotonic()
        self.history = [(t, line) for t, line in self.history[-60:] if now - t <= 8]

    def recent_clues(self) -> list[str]:
        self.poll()
        return [line for _, line in self.history[-_MAX_LINES:]]


class VoiceNickResearch:
    """Local-only JSONL proof records, guarded behind explicit diagnostic opt-in."""
    def __init__(self, voice_path: str | Path, report_path: str | Path):
        self.report_path = Path(report_path)
        self.tailer = LogClueTail(voice_path)
        self.records = 0
        self.last_voice_seq: int | None = None
        self._lock = threading.Lock()

    def observe(self, *, seq: int, seconds: float, origin: str) -> None:
        with self._lock:
            self.last_voice_seq = int(seq)
        if origin != "live":
            return
        self.tailer.poll()
        self._append({
            "event": "incoming_voice",
            "seq": int(seq),
            "seconds": round(float(seconds), 2),
            "identity_status": "unknown",
            "evidence_source": "voice.wav (PCM without talker ID)",
            "console_clues_unverified": self.tailer.recent_clues(),
        })

    def record_screen_frame(self, *, seq_hint: int, file_name: str | None, quality: str) -> None:
        """A visual clue only. No automatic audio-to-nickname assertion."""
        self._append({
            "event": "speaker_screen_sample",
            "voice_seq_hint_not_verified": int(seq_hint),
            "capture_quality": str(quality)[:80],
            "local_frame_file": str(file_name)[:120] if file_name else None,
            "identity_status": "unknown",
            "interpretation": "game HUD screenshot; speaker association not verified",
        })

    def annotate(self, nickname: str) -> bool:
        """Manual ground truth; never automatically assign to other utterances."""
        name = "".join(c for c in str(nickname).strip() if c >= " ")[:40]
        with self._lock:
            last_seq = self.last_voice_seq
        if last_seq is None or not name:
            return False
        self._append({
            "event": "manual_speaker_annotation",
            "seq": int(last_seq),
            "nickname": name,
            "identity_status": "user_verified_for_this_utterance_only",
        })
        return True

    def _append(self, record: dict) -> None:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **record,
        }
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            # Avoid an unbounded permanent test log.
            if self.report_path.exists() and self.report_path.stat().st_size > 3 * 1024 * 1024:
                backup = self.report_path.with_name(self.report_path.name + ".previous")
                os.replace(self.report_path, backup)
            with self.report_path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.records += 1
