"""Quality gate for very short noisy incoming CoD2 voice messages.

Whisper language_probability is a comparative language-detection score, NOT a
calibrated guarantee of ASR accuracy. We therefore display recognized speech
even when the language ranking is weak, clearly marking it as preliminary.
The testable decision logic uses no Windows/audio dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecognitionQuality:
    trustworthy: bool
    reason: str = ""
    tentative: bool = False


def evaluate_transcription(
    text: str,
    language: str,
    language_probability: float,
    segments: list,
    seconds: float,
) -> RecognitionQuality:
    normalized = " ".join(str(text or "").split())
    if len(normalized) < 2:
        return RecognitionQuality(False, "Нет разборчивой фразы")
    if not segments:
        return RecognitionQuality(False, "Whisper не выдал речевых сегментов")

    code = str(language or "").strip().lower()
    if code in ("", "auto", "unknown", "und"):
        return RecognitionQuality(False, "Язык не определён")

    try:
        confidence = float(language_probability)
    except (ValueError, TypeError):
        confidence = 0.0
    if not 0.0 <= confidence <= 1.0:
        confidence = 0.0

    # 8-kHz voice contains noise, packet loss and push-to-talk clicks.
    if all(float(getattr(s, "no_speech_prob", 0) or 0) > 0.72 for s in segments):
        return RecognitionQuality(False, "Вероятно, не речь")
    if all(float(getattr(s, "avg_logprob", 0) or 0) < -1.2 for s in segments):
        return RecognitionQuality(False, "Распознавание очень неуверенное")
    if all(float(getattr(s, "compression_ratio", 0) or 0) > 2.4 for s in segments):
        return RecognitionQuality(False, "Повторяющийся или испорченный текст")

    if normalized.casefold().rstrip(".!?") in {
        "thank you for watching", "thanks for watching",
        "подписывайтесь на канал", "субтитры сделал dimatorzok",
    }:
        return RecognitionQuality(False, "Похоже на типичную галлюцинацию Whisper")

    # A language ranking score is NOT speech transcription accuracy.
    # For short/noisy gaming calls do not discard intelligible text just
    # because the inferred language is uncertain. Retain the transcript
    # with a clearly indicated preliminary label instead.
    tentative = confidence < 0.70
    if tentative:
        return RecognitionQuality(
            True,
            f"Язык {code.upper()} определён неуверенно ({confidence:.1%}); "
            "показываем предварительное распознавание",
            tentative=True,
        )

    return RecognitionQuality(True)
