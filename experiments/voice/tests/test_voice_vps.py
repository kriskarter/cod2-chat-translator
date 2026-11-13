"""Offline, no-model and no-internet tests of secure VPS voice protocol."""
from __future__ import annotations

import base64
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_vps_client import VPSVoiceClient, VPSVoiceError, validate_endpoint
from voice_vps_server import make_handler

TOKEN = "a2d44d2d9c89f1a23287755ee191d3b7f34bdcb673f2"


class StubEngine:
    def __init__(self):
        self.limit = threading.BoundedSemaphore(1)
        self.invocations = 0
        self.last_fast = None

    def recognize(self, pcm, fast):
        self.invocations += 1
        self.last_fast = fast
        return {
            "text": "Easy!",
            "language": "en",
            "language_probability": 0.546,
            "segments": [{
                "no_speech_prob": 0.02,
                "avg_logprob": -0.2,
                "compression_ratio": 1.1,
            }],
            "asr_seconds": 0.12,
        }


class FastVoiceProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = StubEngine()
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(cls.engine, TOKEN)
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        self.client = VPSVoiceClient(self.url, TOKEN, timeout=2)

    def _send(self, payload, token=TOKEN):
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        req = request.Request(
            self.url + "/v1/asr",
            method="POST", headers=headers,
            data=json.dumps(payload).encode("utf-8"),
        )
        try:
            with request.urlopen(req, timeout=2) as response:
                return response.status
        except error.HTTPError as exc:
            return exc.code

    def test_health_is_authenticated(self):
        self.assertTrue(self.client.health())
        with self.assertRaises(VPSVoiceError):
            VPSVoiceClient(self.url, "x" * 32).health()

    def test_roundtrip_easy_kept_at_rounded_55_percent(self):
        data = self.client.transcribe(bytes(16000), fast=True)
        self.assertEqual(data["text"], "Easy!")
        self.assertAlmostEqual(data["language_probability"], .546)
        self.assertEqual(self.engine.last_fast, True)
        self.assertGreaterEqual(data["client_elapsed_seconds"], 0)

    def test_bad_auth_does_not_invoke_engine(self):
        before = self.engine.invocations
        self.assertEqual(
            self._send({"audio_b64": base64.b64encode(bytes(3200)).decode()}, "x" * 32),
            401,
        )
        self.assertEqual(self.engine.invocations, before)

    def test_invalid_base64_rejected(self):
        self.assertEqual(self._send({"audio_b64": "@@@"}), 400)

    def test_oversized_audio_rejected(self):
        self.assertEqual(
            self._send({"audio_b64": base64.b64encode(bytes(192002)).decode()}),
            400,
        )

    def test_busy_server_refuses_simultaneous_jobs(self):
        self.engine.limit.acquire()
        try:
            self.assertEqual(
                self._send({"audio_b64": base64.b64encode(bytes(3200)).decode()}),
                503,
            )
        finally:
            self.engine.limit.release()

    def test_unencrypted_public_url_rejected(self):
        with self.assertRaises(ValueError):
            validate_endpoint("http://example.com:8765")
        with self.assertRaises(ValueError):
            validate_endpoint("http://192.0.2.100:8765")
        self.assertEqual(validate_endpoint("https://voice.example.org"), "https://voice.example.org")
        self.assertEqual(validate_endpoint("http://localhost:8765"), "http://localhost:8765")

    def test_auth_token_required_and_not_echoed(self):
        with self.assertRaises(ValueError):
            VPSVoiceClient(self.url, "short")
        with self.assertRaises(ValueError):
            validate_endpoint("https://user:password@example.com")

    def test_local_fallback_after_connection_error_can_be_selected(self):
        c = VPSVoiceClient("http://127.0.0.1:1", TOKEN, timeout=1)
        with self.assertRaises(VPSVoiceError):
            c.transcribe(bytes(3200), fast=True)
        with self.assertRaisesRegex(VPSVoiceError, "temporary_backoff"):
            c.transcribe(bytes(3200), fast=True)


if __name__ == "__main__":
    unittest.main()
