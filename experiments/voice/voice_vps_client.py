"""Windows client for optional CoD2 VPS Fast Voice.

Uses HTTPS, or loopback HTTP through a user-owned SSH tunnel. Credentials
live only in RAM. Failed remote requests cause local ASR fallback.
"""
from __future__ import annotations

import base64
import ipaddress
import json
import threading
import time
from urllib import error, parse, request


class VPSVoiceError(RuntimeError):
    pass


def validate_endpoint(url: str) -> str:
    """Refuse unencrypted remote voice upload and credential-bearing URLs."""
    url = str(url).strip().rstrip("/")
    parts = parse.urlsplit(url)
    if (
        parts.scheme not in ("https", "http")
        or not parts.hostname or parts.username or parts.password
        or parts.query or parts.fragment or parts.path not in ("", "/")
    ):
        raise ValueError("VPS URL: укажи HTTPS-адрес без пути и параметров.")
    try:
        loopback = ipaddress.ip_address(parts.hostname).is_loopback
    except ValueError:
        loopback = parts.hostname.lower() == "localhost"
    if parts.scheme == "http" and not loopback:
        raise ValueError("Передача аудио по HTTP разрешена только на localhost (SSH-туннель).")
    if not 1 <= (parts.port or 443) <= 65535:
        raise ValueError("Некорректный порт VPS.")
    return url


class VPSVoiceClient:
    def __init__(self, url: str, token: str, *, timeout: float = 7.5):
        self.url = validate_endpoint(url)
        if len(token) < 32 or any(x in token for x in ("\r", "\n")):
            raise ValueError("Токен VPS должен содержать минимум 32 символа.")
        self.token = token
        self.timeout = max(1.0, min(15.0, float(timeout)))
        self._retry_after = 0.0
        self._lock = threading.Lock()

    def _request(self, method: str, path: str, payload: bytes | None = None) -> dict:
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(self.url + path, data=payload, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                if response.status != 200:
                    raise VPSVoiceError("remote_unavailable")
                data = response.read(64 * 1024 + 1)
                if len(data) > 64 * 1024:
                    raise VPSVoiceError("response_too_large")
                reply = json.loads(data)
                if not isinstance(reply, dict):
                    raise VPSVoiceError("bad_response")
                return reply
        except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
            # Never echo URL, token or response body into game logs.
            code = "HTTP_" + str(exc.code) if isinstance(exc, error.HTTPError) else type(exc).__name__
            raise VPSVoiceError(code) from None

    def health(self) -> bool:
        return self._request("GET", "/healthz").get("status") == "ready"

    def transcribe(self, pcm: bytes, *, fast: bool) -> dict:
        with self._lock:
            if time.monotonic() < self._retry_after:
                raise VPSVoiceError("temporary_backoff")
        if not pcm or len(pcm) % 2 or len(pcm) > 192_000:
            raise VPSVoiceError("invalid_audio")
        payload = json.dumps({
            "audio_b64": base64.b64encode(pcm).decode("ascii"),
            "fast": bool(fast),
        }, separators=(",", ":")).encode("utf-8")
        start = time.monotonic()
        try:
            result = self._request("POST", "/v1/asr", payload)
            if (
                not isinstance(result.get("text"), str)
                or not isinstance(result.get("language"), str)
                or not isinstance(result.get("segments"), list)
                or not isinstance(result.get("language_probability"), (int, float))
            ):
                raise VPSVoiceError("invalid_transcript")
            result["client_elapsed_seconds"] = time.monotonic() - start
            with self._lock:
                self._retry_after = 0.0
            return result
        except VPSVoiceError:
            with self._lock:
                self._retry_after = time.monotonic() + 12.0
            raise
