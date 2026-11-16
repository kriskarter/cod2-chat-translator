"""Experimental low-resource Russian STT using a local 45 MB Vosk model.

This is NOT an automatic multilingual replacement for Whisper. It is offered
as a separate user-selected benchmark for Russian-only CoD2 conversations.

The official model download is hash-verified and extracted with path/size caps.
No user audio is uploaded by this engine.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path

import numpy as np

MODEL_NAME = "Vosk RU · быстрый тест"
MODEL_ID = "vosk-model-small-ru-0.22"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
# SHA-256 cross-published by the community HF mirror of the official model.
EXPECTED_SHA256 = "961d5ff98a17f4aa6de69864d0aa71fa5bac682301d2b5d17a3f24c5c99a46d4"
MAX_DOWNLOAD_BYTES = 60 * 1024 * 1024
MAX_UNPACK_BYTES = 300 * 1024 * 1024
REQUIRED_SUBDIRS = ("am", "conf", "graph", "ivector")


def is_vosk_model(name: str) -> bool:
    return name == MODEL_NAME


def has_valid_model(path: Path) -> bool:
    return path.is_dir() and all((path / subdir).is_dir() for subdir in REQUIRED_SUBDIRS)


def safe_model_files(items: list[zipfile.ZipInfo]) -> list[zipfile.ZipInfo]:
    """Reject ZIP-slip, duplicates and oversized archives before extraction."""
    total = 0
    seen: set[str] = set()
    for item in items:
        name = item.filename.replace("\\", "/")
        parts = Path(name).parts
        if (
            not parts or parts[0] != MODEL_ID or Path(name).is_absolute()
            or ".." in parts or ":" in name or "\x00" in name
        ):
            raise ValueError("Unexpected path in Vosk model archive")
        if stat.S_ISLNK((item.external_attr >> 16) & 0xFFFF):
            raise ValueError("Symlinks not permitted in Vosk model archive")
        if not item.is_dir():
            total += item.file_size
            if item.file_size > 90 * 1024 * 1024 or total > MAX_UNPACK_BYTES:
                raise ValueError("Unexpected Vosk archive size")
        if name in seen:
            raise ValueError("Duplicated entry in Vosk archive")
        seen.add(name)
    return items


def ensure_vosk_model(cache_root: Path, status=None) -> Path:
    """Download only on explicit Vosk selection and then reuse cached folder."""
    cache_root = Path(cache_root)
    target = cache_root / MODEL_ID
    if has_valid_model(target):
        return target

    import requests

    cache_root.mkdir(parents=True, exist_ok=True)
    staged_zip = cache_root / (MODEL_ID + ".download")
    staged_dir = cache_root / (MODEL_ID + ".unpacking")
    if staged_dir.exists():
        shutil.rmtree(staged_dir)
    if status:
        status("Vosk RU: загружаю модель 45 МБ, один раз…")
    try:
        sha = hashlib.sha256()
        count = 0
        with requests.get(
            MODEL_URL, stream=True, timeout=(8, 60),
            headers={"User-Agent": "CoD2-Voice-Prototype/1.0"},
        ) as response:
            response.raise_for_status()
            with staged_zip.open("wb") as output:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if not chunk:
                        continue
                    count += len(chunk)
                    if count > MAX_DOWNLOAD_BYTES:
                        raise ValueError("Downloaded model archive is unexpectedly large")
                    sha.update(chunk)
                    output.write(chunk)

        if sha.hexdigest() != EXPECTED_SHA256:
            raise ValueError(
                "Model checksum mismatch. Download not installed; try again later."
            )

        if status:
            status("Vosk RU: проверяю и распаковываю модель…")
        with zipfile.ZipFile(staged_zip) as archive:
            entries = safe_model_files(archive.infolist())
            staged_dir.mkdir()
            for entry in entries:
                dest = staged_dir / Path(entry.filename).relative_to(MODEL_ID)
                if entry.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as source, dest.open("wb") as result:
                        shutil.copyfileobj(source, result, 128 * 1024)
        if not has_valid_model(staged_dir):
            raise ValueError("Incomplete Vosk model archive")
        if target.exists():
            shutil.rmtree(target)
        os.replace(staged_dir, target)
        return target
    finally:
        staged_zip.unlink(missing_ok=True)
        if staged_dir.exists():
            shutil.rmtree(staged_dir)


def raw_8khz_to_pcm16_16khz(raw: bytes) -> bytes:
    """Resample headerless signed 16-bit PCM at 8kHz to signed 16kHz."""
    if len(raw) % 2:
        raw = raw[:-1]
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32)
    if len(samples) < 2:
        return b""
    n = len(samples) * 2
    positions = np.arange(n, dtype=np.float64) / 2
    values = np.interp(positions, np.arange(len(samples)), samples)
    return np.clip(np.rint(values), -32768, 32767).astype("<i2").tobytes()


def decode_result_json(result: str) -> str:
    """Aggregate Vosk final results, without inventing language probability."""
    data = json.loads(result)
    if not isinstance(data, dict):
        return ""
    text = str(data.get("text") or "").strip()
    return " ".join(text.split())


def recognize_vosk(model, raw_pcm_8khz: bytes) -> str:
    from vosk import KaldiRecognizer

    samples = raw_8khz_to_pcm16_16khz(raw_pcm_8khz)
    if not samples:
        return ""
    recog = KaldiRecognizer(model, 16000)
    words = []
    for i in range(0, len(samples), 16000):
        if recog.AcceptWaveform(samples[i:i + 16000]):
            partial = decode_result_json(recog.Result())
            if partial:
                words.append(partial)
    final = decode_result_json(recog.FinalResult())
    if final:
        words.append(final)
    return " ".join(words).strip()


def vosk_quality_reason(text: str) -> str | None:
    if len(" ".join(text.split())) < 2:
        return "Vosk не распознал разборчивую фразу"
    if len(text.split()) > 45:
        return "Необычно длинная гипотеза Vosk"
    return None
