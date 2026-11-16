"""Loopback-only, authenticated CoD2 speech-recognition service.

Never stores, forwards or logs incoming audio; returns transcription only.
Publish it through an authenticated encrypted tunnel, not bare HTTP on the Internet.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hmac
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_SECONDS = 12
SAMPLE_RATE = 8000
MAX_AUDIO_BYTES = MAX_SECONDS * SAMPLE_RATE * 2
MAX_BODY_BYTES = 280_000


class Busy(Exception):
    pass


class FastVoiceEngine:
    def __init__(self, *, model_name: str = "tiny", cpu_threads: int = 2):
        from faster_whisper import WhisperModel
        self.cpu_threads = max(1, min(4, cpu_threads))
        self.model = WhisperModel(
            model_name, device="cpu", compute_type="int8",
            cpu_threads=self.cpu_threads, num_workers=1,
        )
        self.limit = threading.BoundedSemaphore(1)

    def recognize(self, pcm: bytes, fast: bool) -> dict:
        import numpy as np
        # PCM signed 16-bit LE at 8 kHz; Whisper requires 16 kHz float32.
        src = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        samples = np.interp(
            np.arange(len(src) * 2, dtype=np.float32) / 2,
            np.arange(len(src), dtype=np.float32),
            src,
        ).astype(np.float32)
        opts = {
            "beam_size": 1 if fast else 2,
            "best_of": 1 if fast else 2,
            "without_timestamps": True,
            "condition_on_previous_text": False,
            "vad_filter": False,
            "temperature": 0.0,
        }
        t0 = time.monotonic()
        segments, info = self.model.transcribe(samples, language=None, **opts)
        segments = list(segments)
        elapsed = round(time.monotonic() - t0, 3)
        return {
            "text": " ".join(s.text.strip() for s in segments if s.text.strip()).strip(),
            "language": str(info.language or "und"),
            "language_probability": float(info.language_probability or 0),
            "segments": [
                {
                    "no_speech_prob": float(getattr(s, "no_speech_prob", 0) or 0),
                    "avg_logprob": float(getattr(s, "avg_logprob", 0) or 0),
                    "compression_ratio": float(getattr(s, "compression_ratio", 0) or 0),
                }
                for s in segments[:40]
            ],
            "asr_seconds": elapsed,
        }


def make_handler(engine, secret: str):
    """Dependency-injected handler so routing/security can be tested without models."""
    if len(secret) < 32:
        raise ValueError("COD2_VOICE_TOKEN must be at least 32 characters")

    class Handler(BaseHTTPRequestHandler):
        server_version = "CoD2FastVoice/1"
        sys_version = ""

        def log_message(self, format, *args):
            # No request path, IP or bearer token in logs.
            pass

        def _json(self, status: int, payload: dict):
            raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def _authenticated(self):
            authorization = self.headers.get("Authorization", "")
            expected = "Bearer " + secret
            return hmac.compare_digest(authorization, expected)

        def do_GET(self):
            if not self._authenticated():
                self._json(401, {"error": "unauthorized"})
            elif self.path == "/healthz":
                self._json(200, {"status": "ready", "version": 1})
            else:
                self._json(404, {"error": "not_found"})

        def do_POST(self):
            if not self._authenticated():
                self._json(401, {"error": "unauthorized"})
                return
            if self.path != "/v1/asr":
                self._json(404, {"error": "not_found"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 0
            if not 0 < size <= MAX_BODY_BYTES:
                self.close_connection = True
                self._json(413, {"error": "payload_too_large"})
                return
            body = self.rfile.read(size)
            try:
                doc = json.loads(body)
                if not isinstance(doc, dict) or not isinstance(doc.get("audio_b64"), str):
                    raise ValueError("bad_payload")
                pcm = base64.b64decode(doc["audio_b64"], validate=True)
                if not 3200 <= len(pcm) <= MAX_AUDIO_BYTES or len(pcm) % 2:
                    raise ValueError("bad_audio_duration")
                if not isinstance(doc.get("fast", True), bool):
                    raise ValueError("bad_mode")
            except (ValueError, TypeError, binascii.Error, UnicodeError):
                self._json(400, {"error": "bad_audio"})
                return
            if not engine.limit.acquire(blocking=False):
                self._json(503, {"error": "busy"})
                return
            try:
                data = engine.recognize(pcm, bool(doc.get("fast", True)))
                self._json(200, data)
            except Exception:
                # Avoid details from the inference library appearing over the wire.
                self._json(500, {"error": "asr_failed"})
            finally:
                engine.limit.release()

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="CoD2 Fast Voice loopback-only ASR")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", choices=("tiny", "base"), default="tiny")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    secret = os.environ.get("COD2_VOICE_TOKEN", "")
    if len(secret) < 32:
        parser.error("Set COD2_VOICE_TOKEN to a random value with at least 32 chars")
    engine = FastVoiceEngine(model_name=args.model, cpu_threads=args.threads)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(engine, secret))
    print("CoD2 Fast Voice ready on localhost only; no audio is stored.", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
