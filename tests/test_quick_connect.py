from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

from server_catalog import SERVER_ADDRESS, build_connect_command, find_multiplayer_executable, launch_connect_command, unique_roots


class QuickConnectTests(unittest.TestCase):
    def test_find_multiplayer_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "CoD2MP_s.exe"
            exe.write_bytes(b"test")
            self.assertEqual(find_multiplayer_executable([root]), exe.resolve(strict=False))

    def test_build_connect_command(self):
        exe = Path(r"C:\\Games\\Call of Duty 2\\CoD2MP_s.exe")
        self.assertEqual(build_connect_command(exe), [str(exe), "+connect", SERVER_ADDRESS])

    def test_normal_quick_connect_uses_process_launch(self):
        exe = Path(r"C:\\Games\\Call of Duty 2\\CoD2MP_s.exe")
        with mock.patch("server_catalog.subprocess.Popen") as popen:
            launch_connect_command(exe)
        popen.assert_called_once()

    def test_unique_roots_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(len(unique_roots([root, root, str(root)])), 1)


if __name__ == "__main__":
    unittest.main()
