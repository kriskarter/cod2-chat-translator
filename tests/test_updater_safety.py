import hashlib
import tempfile
import unittest
from pathlib import Path

import updater


class UpdaterSafetyTests(unittest.TestCase):
    def test_archive_member_safety(self):
        self.assertEqual(updater.unsafe_archive_members(["CoD2ChatTranslator.exe", "folder/file.txt"]), [])
        bad = updater.unsafe_archive_members(["../evil.exe", "folder/../../evil.dll", r"C:\\evil.exe"])
        self.assertEqual(len(bad), 3)

    def test_updater_uses_elevated_windows_launch(self):
        source = (
            Path(updater.__file__)
            .read_text(encoding="utf-8")
        )

        self.assertIn(
            '"runas"',
            source,
        )

        self.assertIn(
            "ShellExecuteW",
            source,
        )

        self.assertIn(
            "launch_updated_application(",
            source,
        )


    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.bin"
            p.write_bytes(b"cod2")
            self.assertEqual(updater.sha256_file(p), hashlib.sha256(b"cod2").hexdigest())


if __name__ == "__main__":
    unittest.main()
