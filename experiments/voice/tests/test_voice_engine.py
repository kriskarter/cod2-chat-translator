"""Voice pipeline tests: no model downloads, network, or Windows needed."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_engine import (
    BYTE_RATE, FileTail, LiveCollector, split_utterances, to_whisper_audio
)


def tone(seconds: float, amplitude: int = 1500) -> bytes:
    x = np.arange(round(seconds * 8000), dtype=np.float64)
    return (np.sin(2 * np.pi * 380 * x / 8000) * amplitude).astype("<i2").tobytes()


class FileTailTests(unittest.TestCase):
    def test_existing_history_is_skipped_and_append_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "voice.wav"
            p.write_bytes(b"\x01\x00" * 8000)
            tail = FileTail(p)
            self.assertEqual(tail.read_new(), b"")
            with p.open("ab") as f:
                f.write(b"\x03\x00" * 320)
            self.assertEqual(tail.read_new(), b"\x03\x00" * 320)
            self.assertEqual(tail.read_new(), b"")

    def test_file_created_after_start_includes_first_voice(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "voice.wav"
            tail = FileTail(p)
            self.assertEqual(tail.read_new(), b"")
            p.write_bytes(b"\x01\x00" * 300)
            self.assertEqual(tail.read_new(), b"\x01\x00" * 300)

    def test_truncation_starts_again_at_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "voice.wav"
            p.write_bytes(b"\x02\x00" * 500)
            tail = FileTail(p)
            p.write_bytes(b"\x05\x00" * 100)
            self.assertEqual(tail.read_new(), b"\x05\x00" * 100)

    def test_from_start_replays_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "voice.wav"
            p.write_bytes(b"\x01\x00" * 200)
            tail = FileTail(p, from_start=True)
            self.assertEqual(tail.read_new(), b"\x01\x00" * 200)

    def test_incomplete_sample_is_read_on_later_tick(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "voice.wav"
            tail = FileTail(p)
            p.write_bytes(b"\x01")
            self.assertEqual(tail.read_new(), b"")
            with p.open("ab") as f:
                f.write(b"\x02")
            self.assertEqual(tail.read_new(), b"\x01\x02")


class CollectorTests(unittest.TestCase):
    def test_idle_speech_boundary(self):
        c = LiveCollector(idle_seconds=0.8)
        self.assertEqual(c.feed(tone(.5), now=1.0), [])
        self.assertIsNone(c.flush_if_idle(now=1.6))
        out = c.flush_if_idle(now=1.9)
        self.assertEqual(len(out), 8000)
        self.assertIsNone(c.flush_if_idle(now=2.0))

    def test_max_length_caps_memory(self):
        c = LiveCollector(max_seconds=1.0)
        out = c.feed(tone(2.3), now=1.0)
        self.assertEqual([len(x) for x in out], [BYTE_RATE, BYTE_RATE])
        self.assertEqual(len(c.buffer), int(.3 * BYTE_RATE))


class SegmentationTests(unittest.TestCase):
    def test_silence_and_two_phrases(self):
        raw = b"\0" * BYTE_RATE + tone(1.0) + b"\0" * (BYTE_RATE * 2) + tone(1.1)
        clips = split_utterances(raw)
        self.assertEqual(len(clips), 2)
        self.assertTrue(all(len(x) > BYTE_RATE // 2 for x in clips))

    def test_entire_silence_is_ignored(self):
        self.assertEqual(split_utterances(bytes(BYTE_RATE * 3)), [])

    def test_odd_pcm_bytes_rejected(self):
        self.assertEqual(split_utterances(b"\x01"), [])
        with self.assertRaises(ValueError):
            to_whisper_audio(b"\x01")

    def test_correct_resampled_length_and_dtype(self):
        data = to_whisper_audio(tone(1.25))
        self.assertEqual(data.dtype, np.float32)
        self.assertEqual(len(data), 20000)
        self.assertLessEqual(float(np.max(np.abs(data))), 1.0)


if __name__ == "__main__":
    unittest.main()
