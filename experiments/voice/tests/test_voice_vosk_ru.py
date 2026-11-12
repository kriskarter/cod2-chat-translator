"""Vosk RU benchmarking module tests: fast, offline, no model download."""
from __future__ import annotations

import hashlib
import io
import json
import stat
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voice_vosk_ru as module


def demo_zip() -> bytes:
    """Synthetic package implementing expected directory layout."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in module.REQUIRED_SUBDIRS:
            z.writestr(f"{module.MODEL_ID}/{name}/example", b"demo")
    return out.getvalue()


class VoskTests(unittest.TestCase):
    def test_manual_russian_model_is_not_automatic_multilingual(self):
        self.assertTrue(module.is_vosk_model(module.MODEL_NAME))
        self.assertFalse(module.is_vosk_model("tiny"))
        self.assertFalse(module.is_vosk_model("base"))

    def test_raw_8khz_to_16khz_pcm_mono(self):
        raw = np.array([0, 1000, -1000, 0], dtype="<i2").tobytes()
        output = module.raw_8khz_to_pcm16_16khz(raw)
        values = np.frombuffer(output, dtype="<i2")
        self.assertEqual(len(values), 8)
        self.assertEqual(int(values[0]), 0)
        self.assertEqual(int(values[2]), 1000)
        self.assertEqual(int(values[4]), -1000)

    def test_unsafe_archives_rejected_before_extraction(self):
        with self.assertRaises(ValueError):
            module.safe_model_files([zipfile.ZipInfo("../secret")])
        with self.assertRaises(ValueError):
            module.safe_model_files([zipfile.ZipInfo("evil/file")])
        with self.assertRaises(ValueError):
            module.safe_model_files([
                zipfile.ZipInfo(module.MODEL_ID + "/file"),
                zipfile.ZipInfo(module.MODEL_ID + "/file"),
            ])
        link = zipfile.ZipInfo(module.MODEL_ID + "/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            module.safe_model_files([link])

    def test_model_download_hash_and_cache_idempotency(self):
        archive = demo_zip()
        expected = hashlib.sha256(archive).hexdigest()

        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                return False
            def raise_for_status(self):
                return None
            def iter_content(self, chunk_size):
                yield archive[:77]
                yield archive[77:]

        fake_requests = types.ModuleType("requests")
        calls = []
        def fake_get(*a, **k):
            calls.append((a, k))
            return FakeResponse()
        fake_requests.get = fake_get

        with tempfile.TemporaryDirectory() as folder, patch.object(
            module, "EXPECTED_SHA256", expected
        ), patch.dict(sys.modules, {"requests": fake_requests}):
            path = module.ensure_vosk_model(Path(folder), status=lambda _: None)
            self.assertTrue(module.has_valid_model(path))
            self.assertEqual(len(calls), 1)
            again = module.ensure_vosk_model(Path(folder))
            self.assertEqual(path, again)
            self.assertEqual(len(calls), 1)

    def test_corrupt_model_checksum_never_installed(self):
        archive = demo_zip()

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def raise_for_status(self): return None
            def iter_content(self, **k): yield archive

        fake_requests = types.ModuleType("requests")
        fake_requests.get = lambda *a, **k: FakeResponse()
        with tempfile.TemporaryDirectory() as folder, patch.object(
            module, "EXPECTED_SHA256", "0" * 64
        ), patch.dict(sys.modules, {"requests": fake_requests}):
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                module.ensure_vosk_model(Path(folder))
            self.assertFalse(module.has_valid_model(Path(folder) / module.MODEL_ID))

    def test_vosk_decode_short_russian(self):
        seen = []

        class FakeRecognizer:
            def __init__(self, model, sample_rate):
                seen.append(sample_rate)
            def AcceptWaveform(self, data):
                seen.append(len(data))
                return False
            def FinalResult(self):
                return json.dumps({"text": "привет земляк"})

        fake_vosk = types.ModuleType("vosk")
        fake_vosk.KaldiRecognizer = FakeRecognizer
        raw = np.array([0, 100, -100, 0] * 100, dtype="<i2").tobytes()
        with patch.dict(sys.modules, {"vosk": fake_vosk}):
            text = module.recognize_vosk(object(), raw)
        self.assertEqual(text, "привет земляк")
        self.assertEqual(seen[0], 16000)
        self.assertEqual(sum(seen[1:]), len(raw) * 2)

    def test_no_confidence_is_invented_from_quality_gate(self):
        self.assertIsNone(module.vosk_quality_reason("привет земляк"))
        self.assertIsNotNone(module.vosk_quality_reason(""))
        self.assertIsNone(module.vosk_quality_reason("да"))
        self.assertIsNotNone(module.vosk_quality_reason("я"))


if __name__ == "__main__":
    unittest.main()
