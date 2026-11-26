"""Explicit, atomic Qt settings persistence; never overwrite the source config."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path


class SettingsStore:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser().resolve()
        self._expected = self.path.read_bytes() if self.path.exists() else None

    def load(self, defaults):
        if self._expected is None:
            return defaults
        data = json.loads(self._expected.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Settings must be an object")
        from app import deep_merge
        return deep_merge(defaults, data)

    def save(self, data):
        current = self.path.read_bytes() if self.path.exists() else None
        if current != self._expected:
            raise RuntimeError("Settings changed outside this application; save cancelled")
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.replace(name, self.path)
            self._expected = payload
        finally:
            if os.path.exists(name):
                os.unlink(name)
