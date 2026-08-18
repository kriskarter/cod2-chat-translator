import base64
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from update_client import (
    update_signature_payload,
    verify_update_manifest_signature,
)


class UpdateSignatureTests(unittest.TestCase):

    def manifest(self):
        return {
            "version": "9.9.9",
            "asset": "CoD2ChatTranslator_Update.zip",
            "sha256": "a" * 64,
            "notes_ru": "test",
            "notes_en": "test",
            "signature_alg": "ed25519",
            "signature_key_id": "test-key",
        }

    def signed(self):
        private = Ed25519PrivateKey.generate()

        public_der = private.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        manifest = self.manifest()

        manifest["signature"] = base64.b64encode(
            private.sign(
                update_signature_payload(manifest)
            )
        ).decode("ascii")

        keys = {
            "test-key":
                base64.b64encode(public_der).decode("ascii")
        }

        return manifest, keys

    def test_valid_signature(self):
        manifest, keys = self.signed()

        self.assertTrue(
            verify_update_manifest_signature(
                manifest,
                keys,
            )
        )

    def test_modified_hash_rejected(self):
        manifest, keys = self.signed()

        manifest["sha256"] = "b" * 64

        self.assertFalse(
            verify_update_manifest_signature(
                manifest,
                keys,
            )
        )

    def test_unsigned_manifest_rejected(self):
        manifest = self.manifest()

        self.assertFalse(
            verify_update_manifest_signature(
                manifest,
                {},
            )
        )


if __name__ == "__main__":
    unittest.main()
