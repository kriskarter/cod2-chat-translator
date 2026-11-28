"""Atomic Qt settings, optimistic concurrency and last-valid backup."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path


def _read(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _decode(payload):
    data = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Settings must be an object")
    return data


def _atomic_write(path, payload):
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class SettingsStore:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
        self.backup = self.path.with_name(self.path.name + ".bak")
        self._expected = _read(self.path)
        self.recovered = False

    def load(self, defaults):
        if self._expected is None:
            return defaults
        try:
            data = _decode(self._expected)
        except (UnicodeError, ValueError):
            backup = _read(self.backup)
            if backup is None:
                raise
            data = _decode(backup)
            self.recovered = True
        from app import deep_merge
        return deep_merge(defaults, data)

    def save(self, data):
        current = _read(self.path)
        if current != self._expected:
            raise RuntimeError("Settings changed outside this application; save cancelled")
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        _decode(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Preserve the last valid primary file before replacing it. Never
        # overwrite a good backup with corrupt or unreadable bytes.
        if current is not None:
            try:
                _decode(current)
            except (UnicodeError, ValueError):
                pass
            else:
                _atomic_write(self.backup, current)
        _atomic_write(self.path, payload)
        self._expected = payload
        self.recovered = False
