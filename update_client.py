from __future__ import annotations

import base64
import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

GITHUB_API = "https://api.github.com"

UPDATE_SIGNING_KEY_ID = "ed25519-545818c64aa3"

UPDATE_SIGNING_PUBLIC_KEYS = {
    UPDATE_SIGNING_KEY_ID: "MCowBQYDK2VwAyEAylTnyQ4PKCDV82e5gNmPtkJ3+TBhRfXxiGykeINf+ME=",
}

SIGNED_UPDATE_FIELDS = (
    "version",
    "asset",
    "sha256",
    "notes_ru",
    "notes_en",
    "signature_alg",
    "signature_key_id",
)

SIGNED_UPDATE_FIELDS_V2 = (
    "version",
    "asset",
    "sha256",
    "notes_ru",
    "notes_uk",
    "notes_en",
    "signature_alg_v2",
    "signature_key_id_v2",
)


def update_signature_payload(manifest: dict) -> bytes:
    payload = {
        name: str(manifest.get(name) or "")
        for name in SIGNED_UPDATE_FIELDS
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def update_signature_payload_v2(
    manifest: dict,
) -> bytes:
    payload = {
        name: str(manifest.get(name) or "")
        for name in SIGNED_UPDATE_FIELDS_V2
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _verify_manifest_signature(
    manifest: dict,
    *,
    public_keys: dict[str, str] | None,
    algorithm_field: str,
    key_id_field: str,
    signature_field: str,
    payload: bytes,
) -> bool:
    try:
        if (
            str(
                manifest.get(algorithm_field)
                or ""
            ).lower()
            != "ed25519"
        ):
            return False

        manifest_key_id = str(
            manifest.get(key_id_field)
            or ""
        )

        signature_text = str(
            manifest.get(signature_field)
            or ""
        )

        keys = (
            public_keys
            or UPDATE_SIGNING_PUBLIC_KEYS
        )

        encoded_public_key = keys.get(
            manifest_key_id
        )

        if (
            not encoded_public_key
            or not signature_text
        ):
            return False

        public_der = base64.b64decode(
            encoded_public_key,
            validate=True,
        )

        signature = base64.b64decode(
            signature_text,
            validate=True,
        )

        public_key = (
            serialization.load_der_public_key(
                public_der
            )
        )

        if not isinstance(
            public_key,
            Ed25519PublicKey,
        ):
            return False

        public_key.verify(
            signature,
            payload,
        )

        return True

    except Exception:
        return False


def verify_update_manifest_signature(
    manifest: dict,
    public_keys: dict[str, str] | None = None,
) -> bool:
    # V1 remains mandatory so old installed clients
    # can verify the same release manifest.
    if not _verify_manifest_signature(
        manifest,
        public_keys=public_keys,
        algorithm_field="signature_alg",
        key_id_field="signature_key_id",
        signature_field="signature",
        payload=update_signature_payload(
            manifest
        ),
    ):
        return False

    notes_uk = str(
        manifest.get("notes_uk")
        or ""
    )

    has_v2 = any(
        str(manifest.get(name) or "")
        for name in (
            "signature_alg_v2",
            "signature_key_id_v2",
            "signature_v2",
        )
    )

    # Old manifests without Ukrainian notes remain valid.
    if not notes_uk and not has_v2:
        return True

    # New multilingual manifests must protect notes_uk too.
    return _verify_manifest_signature(
        manifest,
        public_keys=public_keys,
        algorithm_field="signature_alg_v2",
        key_id_field="signature_key_id_v2",
        signature_field="signature_v2",
        payload=update_signature_payload_v2(
            manifest
        ),
    )



@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    sha256: str
    asset_name: str
    notes_ru: str = ""
    notes_en: str = ""
    notes_uk: str = ""

    def notes_for_language(
        self,
        language: str,
    ) -> str:
        language = str(language or "").lower()

        if language == "uk":
            return self.notes_uk

        if language == "ru":
            return self.notes_ru

        return self.notes_en


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
    if not verify_update_manifest_signature(manifest):
        raise ValueError("Update manifest signature verification failed")
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
        notes_uk=str(manifest.get("notes_uk") or ""),
    )
