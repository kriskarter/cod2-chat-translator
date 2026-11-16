"""Fast/accurate voice recognition trade-offs and live queue freshness.

Pure helpers are deliberately kept independent of Windows and Whisper so that
latency decisions can be unit-tested without a GPU or model download.
"""
from __future__ import annotations

import queue


def asr_profile(fast: bool) -> dict:
    """Fast mode favors one decoder candidate, while quality mode keeps two."""
    return {
        "beam_size": 1 if fast else 2,
        "best_of": 1 if fast else 2,
        "without_timestamps": True,
        "condition_on_previous_text": False,
        "vad_filter": False,
        "temperature": 0.0,
    }


def capture_idle_seconds(fast: bool) -> float:
    """Wait just long enough for normal push-to-talk packet jitter."""
    return 0.48 if fast else 0.85


def discard_pending(q: queue.Queue, max_pending: int = 0) -> int:
    """Drop only not-yet-started queued work; never interrupt active inference."""
    dropped = 0
    while q.qsize() > max_pending:
        try:
            q.get_nowait()
            q.task_done()
            dropped += 1
        except queue.Empty:
            break
    return dropped
