import json
import tempfile
import threading
import unittest
from pathlib import Path

import app


class BrandingTests(unittest.TestCase):
    def test_v1152_branding(self):
        self.assertEqual(app.APP_VERSION, "1.15.2")
        self.assertEqual(app.PROJECT_AUTHOR, "kriskarter")
        self.assertEqual(app.PROJECT_PROFILE_URL, "https://github.com/kriskarter")
        self.assertEqual(app.UI_STRINGS["ru"]["about"], "О программе")
        self.assertEqual(app.UI_STRINGS["en"]["about"], "About")

        self.assertEqual(app.MAX_OVERLAY_MESSAGES, 5)
        self.assertGreaterEqual(app.recommended_overlay_height(5, 10), 200)

    def test_release_config_keeps_developer_metadata(self):
        root = Path(__file__).resolve().parents[1]
        cfg = json.loads((root / "release_config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["developer"], "kriskarter")
        self.assertEqual(cfg["developer_url"], "https://github.com/kriskarter")

    def test_installer_force_closes_running_translator(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "installer" / "CoD2ChatTranslator.iss").read_text(encoding="utf-8")
        self.assertIn("CloseApplications=force", script)
        self.assertIn("RestartApplications=no", script)

    def test_log_tailer_status_can_be_localized(self):
        statuses = []
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "console_mp.log"
            log.write_text("", encoding="utf-8")
            mapping = {
                "watching_log": "Watching log: {path}",
                "waiting_log": "Waiting for console_mp.log…",
            }
            tailer = app.LogTailer(
                path_getter=lambda: log,
                on_message=lambda _msg: None,
                on_status=statuses.append,
                stop_event=threading.Event(),
                status_text=lambda key: mapping[key],
            )
            tailer._switch_path(log)
            self.assertEqual(statuses[-1], f"Watching log: {log}")

    def test_english_status_strings_have_expected_localization(self):
        en = app.UI_STRINGS["en"]
        self.assertEqual(en["watching_log"], "Watching log: {path}")
        self.assertEqual(en["overlay_locked_status"], "Overlay locked: mouse clicks pass through it")
        self.assertEqual(en["update_postponed"], "Update {version} postponed")
        self.assertEqual(app.UI_STRINGS["ru"]["server_auto"], "● Автоматически")
        self.assertEqual(app.UI_STRINGS["en"]["server_auto"], "● Automatic")
        self.assertIn("server settings", app.UI_STRINGS["en"]["server_settings"].lower())


if __name__ == "__main__":
    unittest.main()
