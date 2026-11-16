"""Regression tests for visible CoD2 speech, translation and bounded replay."""
from __future__ import annotations

import queue
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voice_studio
from voice_engine import AudioJob, BYTE_RATE
from voice_studio import VoiceStudio


class FakeWhisper:
    def transcribe(self, samples, **kwargs):
        segment = SimpleNamespace(
            text="Easy!", no_speech_prob=0.02,
            avg_logprob=-0.15, compression_ratio=1.1,
        )
        info = SimpleNamespace(language="en", language_probability=0.546)
        return iter([segment]), info


def bare_studio():
    """Avoid Tk, network, and real ASR while exercising the production worker."""
    studio = VoiceStudio.__new__(VoiceStudio)
    studio.generation = 7
    studio.seq = 0
    studio.model = FakeWhisper()
    studio.current_model_name = "tiny"
    studio.remote_client = None
    studio.jobs = queue.Queue()
    studio.translations = queue.Queue()
    studio.events = queue.Queue()
    return studio


def all_events(q):
    events = []
    while True:
        try:
            events.append(q.get_nowait())
        except queue.Empty:
            return events


class VoiceOutputPipelineTests(unittest.TestCase):
    def run_asr(self, *, translate):
        studio = bare_studio()
        item = AudioJob(
            seq=1, raw_pcm=bytes(BYTE_RATE),
            origin="recording 1/1",
        )
        studio.jobs.put_nowait(
            (studio.generation, item, "tiny", "ru", translate, True)
        )
        worker = threading.Thread(
            target=studio._worker_loop, daemon=True,
            name="VoiceRegressionASR",
        )
        worker.start()
        studio.jobs.join()
        return studio, all_events(studio.events)

    def test_recognized_short_word_is_displayed_when_translate_disabled(self):
        studio, events = self.run_asr(translate=False)
        results = [p for kind, gen, p in events if kind == "result"]
        self.assertEqual(len(results), 1, events)
        self.assertEqual(results[0]["text"], "Easy!")
        self.assertEqual(results[0]["provider"], "off")
        self.assertTrue(results[0]["tentative"])
        self.assertEqual(studio.translations.qsize(), 0)
        self.assertFalse(any(kind == "status" and "NameError" in str(p) for kind, _, p in events))

    def test_recognized_short_word_still_queues_translation(self):
        studio, events = self.run_asr(translate=True)
        results = [p for kind, gen, p in events if kind == "result"]
        self.assertEqual(len(results), 1, events)
        self.assertEqual(results[0]["provider"], "pending")
        self.assertEqual(studio.translations.qsize(), 1)
        job = studio.translations.get_nowait()
        self.assertEqual(job[2:5], ("Easy!", "en", "ru"))
        self.assertTrue(job[-1])
        studio.translations.task_done()

    def test_uncertain_language_translate_loop_autodetects(self):
        studio = bare_studio()
        studio.translations.put_nowait((
            7, 3, "Easy!", "en", "ru",
            time.monotonic(), "Игрок", True,
        ))
        with patch.object(
            voice_studio, "translate_text", return_value=("Легко!", "stub"),
        ) as translate:
            threading.Thread(
                target=studio._translate_loop, daemon=True,
                name="VoiceRegressionTranslation",
            ).start()
            studio.translations.join()
            translate.assert_called_once_with("Easy!", "auto", "ru")
        events = all_events(studio.events)
        result = [p for kind, _, p in events if kind == "translation"]
        self.assertEqual(len(result), 1, events)
        self.assertEqual(result[0]["translation"], "Легко!")

    def test_replay_does_not_queue_30_clips_in_advance(self):
        studio = bare_studio()
        stop = threading.Event()
        fake_clips = [bytes(BYTE_RATE) for _ in range(30)]
        with patch.object(voice_studio, "read_recording", return_value=bytes(16000 * 30)), (
            patch.object(voice_studio, "split_utterances", return_value=fake_clips)
        ):
            thread = threading.Thread(
                target=studio._replay_loop,
                args=(7, stop, Path("sample.raw"), "tiny", "ru", False, True),
                daemon=True,
            )
            thread.start()
            time.sleep(0.05)
            try:
                self.assertLessEqual(studio.jobs.qsize(), 1)
                self.assertTrue(thread.is_alive())
                self.assertLess(studio.seq, 30, "Replay prefetched all old audio")
            finally:
                stop.set()
                thread.join(timeout=1.5)
            self.assertFalse(thread.is_alive(), "Replay must stop on cancellation")


if __name__ == "__main__":
    unittest.main()
