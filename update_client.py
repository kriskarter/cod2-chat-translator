from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    sha256: str
    asset_name: str
    notes_ru: str = ""
    notes_en: str = ""


def version_key(value: str) -> tuple[int, ...]:
    value = (value or "").strip().lower().lstrip("v")
    parts: list[int] = []
    for chunk in value.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits or 0))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:4])


def is_newer(candidate: str, current: str) -> bool:
    return version_key(candidate) > version_key(current)


def _get_json(url: str, timeout: float = 7.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CoD2ChatTranslator-Updater",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def load_release_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def check_github_release(current_version: str, repository: str, timeout: float = 7.0) -> UpdateInfo | None:
    repository = (repository or "").strip().strip("/")
    if not repository or "/" not in repository:
        return None
    release = _get_json(f"{GITHUB_API}/repos/{repository}/releases/latest", timeout=timeout)
    if not isinstance(release, dict):
        return None
    tag = str(release.get("tag_name") or "")
    if not tag or not is_newer(tag, current_version):
        return None

    assets = release.get("assets") or []
    by_name = {str(a.get("name")): a for a in assets if isinstance(a, dict)}
    manifest_asset = by_name.get("update.json")
    if not manifest_asset:
        return None
    manifest_url = str(manifest_asset.get("browser_download_url") or "")
    if not manifest_url:
        return None
    manifest = _get_json(manifest_url, timeout=timeout)
    if not isinstance(manifest, dict):
        return None
    version = str(manifest.get("version") or tag).lstrip("v")
    if not is_newer(version, current_version):
        return None
    asset_name = str(manifest.get("asset") or "CoD2ChatTranslator_Update.zip")
    package_asset = by_name.get(asset_name)
    if not package_asset:
        return None
    download_url = str(package_asset.get("browser_download_url") or "")
    sha256 = str(manifest.get("sha256") or "").lower().strip()
    if not download_url or len(sha256) != 64:
        return None
    return UpdateInfo(
        version=version,
        download_url=download_url,
        sha256=sha256,
        asset_name=asset_name,
        notes_ru=str(manifest.get("notes_ru") or ""),
        notes_en=str(manifest.get("notes_en") or ""),
    )
