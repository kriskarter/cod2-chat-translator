"""Fast quality-gate checks: no model downloads, network or audio needed."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_quality import evaluate_transcription


def segment(no_speech_prob=0.05, avg_logprob=-0.2, compression_ratio=1.1):
    return SimpleNamespace(
        no_speech_prob=no_speech_prob,
        avg_logprob=avg_logprob,
        compression_ratio=compression_ratio,
    )


class QualityTests(unittest.TestCase):
    def test_29_percent_japanese_on_short_noisy_audio_is_not_translated(self):
        verdict = evaluate_transcription("俺がピンか!", "ja", .29, [segment()], 1.3)
        self.assertFalse(verdict.trustworthy)
        self.assertIn("29%", verdict.reason)

    def test_confident_short_russian_game_callout_passes(self):
        self.assertTrue(
            evaluate_transcription("на B", "ru", .84, [segment()], 1.1).trustworthy
        )

    def test_short_uncertain_real_word_is_preserved_as_diagnostic(self):
        self.assertFalse(
            evaluate_transcription("yes", "en", .41, [segment()], 0.55).trustworthy
        )

    def test_long_utterance_accepts_moderate_language_confidence(self):
        self.assertTrue(
            evaluate_transcription("left behind the boxes", "en", .42, [segment()], 5.2).trustworthy
        )

    def test_borderline_easy_is_tentative_when_speech_evidence_is_strong(self):
        verdict = evaluate_transcription("Easy!", "en", .545, [segment()], 1.2)
        self.assertTrue(verdict.trustworthy)
        self.assertTrue(verdict.tentative)
        self.assertIn("Предварительно", verdict.reason)

    def test_borderline_easy_with_weak_acoustics_is_rejected(self):
        verdict = evaluate_transcription(
            "Easy!", "en", .545,
            [segment(no_speech_prob=.65)], 1.2,
        )
        self.assertFalse(verdict.trustworthy)

    def test_short_guess_far_below_threshold_is_rejected(self):
        verdict = evaluate_transcription("Easy!", "en", .40, [segment()], 1.2)
        self.assertFalse(verdict.trustworthy)

    def test_high_confidence_callout_is_not_tentative(self):
        verdict = evaluate_transcription("Easy!", "en", .85, [segment()], 1.2)
        self.assertTrue(verdict.trustworthy)
        self.assertFalse(verdict.tentative)

    def test_hallucination_cannot_be_accepted_as_tentative(self):
        verdict = evaluate_transcription(
            "thank you for watching", "en", .545, [segment()], 1.2,
        )
        self.assertFalse(verdict.trustworthy)

    def test_no_speech_rejected_even_with_high_language_confidence(self):
        self.assertFalse(
            evaluate_transcription("Hello", "en", .99, [segment(no_speech_prob=.95)], 2.2).trustworthy
        )

    def test_garbled_logprob_is_rejected(self):
        self.assertFalse(
            evaluate_transcription("monster kill", "en", .98, [segment(avg_logprob=-1.8)], 2.2).trustworthy
        )

    def test_repetitive_hallucination_rejected(self):
        self.assertFalse(
            evaluate_transcription("hello hello hello", "en", .99, [segment(compression_ratio=3)], 2.2).trustworthy
        )

    def test_empty_segments_rejected(self):
        self.assertFalse(evaluate_transcription("Hello", "en", .99, [], 1.1).trustworthy)

    def test_unknown_language_rejected(self):
        self.assertFalse(evaluate_transcription("Hallo", "auto", .99, [segment()], 2.1).trustworthy)

    def test_online_translation_not_needed_to_evaluate(self):
        self.assertTrue(evaluate_transcription("idę na B", "pl", .88, [segment()], 1.1).trustworthy)


if __name__ == "__main__":
    unittest.main()
