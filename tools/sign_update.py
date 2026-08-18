from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from update_client import (
    UPDATE_SIGNING_KEY_ID,
    update_signature_payload,
)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: sign_update.py <update.json>")

    manifest_path = Path(sys.argv[1])

    private_pem = os.environ.get(
        "UPDATE_SIGNING_PRIVATE_KEY",
        "",
    )

    if not private_pem.strip():
        raise SystemExit(
            "UPDATE_SIGNING_PRIVATE_KEY is missing"
        )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8-sig")
    )

    private_key = serialization.load_pem_private_key(
        private_pem.encode("utf-8"),
        password=None,
    )

    if not isinstance(private_key, Ed25519PrivateKey):
        raise SystemExit("Signing key is not Ed25519")

    manifest["signature_alg"] = "ed25519"
    manifest["signature_key_id"] = UPDATE_SIGNING_KEY_ID

    signature = private_key.sign(
        update_signature_payload(manifest)
    )

    manifest["signature"] = base64.b64encode(
        signature
    ).decode("ascii")

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        f"Signed update manifest: "
        f"{UPDATE_SIGNING_KEY_ID}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
