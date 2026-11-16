"""Low-latency voice helpers: no Whisper download required."""
from __future__ import annotations
import queue
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_performance import asr_profile, capture_idle_seconds, discard_pending


class VoiceLatencyTests(unittest.TestCase):
    def test_fast_decoder_one_candidate(self):
        profile = asr_profile(True)
        self.assertEqual(profile["beam_size"], 1)
        self.assertEqual(profile["best_of"], 1)
        self.assertTrue(profile["without_timestamps"])
        self.assertFalse(profile["condition_on_previous_text"])

    def test_quality_decoder_retains_two_candidates(self):
        profile = asr_profile(False)
        self.assertEqual(profile["beam_size"], 2)
        self.assertEqual(profile["best_of"], 2)

    def test_fast_capture_finishes_earlier(self):
        self.assertLess(capture_idle_seconds(True), capture_idle_seconds(False))
        self.assertGreater(capture_idle_seconds(True), 0.30)

    def test_queue_discards_stale_job_but_keeps_newest_on_add(self):
        q = queue.Queue()
        for x in ("old1", "old2", "old3"):
            q.put_nowait(x)
        self.assertEqual(discard_pending(q), 3)
        q.put_nowait("latest")
        self.assertEqual(q.get_nowait(), "latest")
        q.task_done()
        self.assertEqual(q.unfinished_tasks, 0)

    def test_pending_translation_retains_latest(self):
        q = queue.Queue()
        for x in (1,2,3,4):
            q.put_nowait(x)
        self.assertEqual(discard_pending(q, max_pending=1), 3)
        self.assertEqual(q.get_nowait(), 4)
        q.task_done()
        self.assertEqual(q.unfinished_tasks, 0)


if __name__ == "__main__":
    unittest.main()
