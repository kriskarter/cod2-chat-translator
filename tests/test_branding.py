import json
import tempfile
import threading
import unittest
from pathlib import Path

import app


class BrandingTests(unittest.TestCase):
    def test_v1170_branding(self):
        self.assertEqual(app.APP_VERSION, "1.17.0")
        self.assertEqual(app.PROJECT_AUTHOR, "kriskarter")
        self.assertEqual(app.PROJECT_PROFILE_URL, "https://github.com/kriskarter")
        self.assertEqual(app.UI_STRINGS["ru"]["about"], "О программе")
        self.assertEqual(app.UI_STRINGS["uk"]["about"], "Про програму")
        self.assertEqual(app.UI_STRINGS["en"]["about"], "About")
        self.assertEqual(set(app.UI_STRINGS["uk"]), set(app.UI_STRINGS["ru"]))

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
        self.assertIn(
            "postinstall skipifsilent shellexec",
            script,
        )
        self.assertIn("ShowLanguageDialog=yes", script)
        self.assertIn(
            "LanguageDetectionMethod=uilanguage",
            script,
        )
        self.assertIn('Name: "english"', script)
        self.assertIn('Name: "russian"', script)
        self.assertIn('Name: "ukrainian"', script)
        self.assertIn("Ukrainian.isl", script)
        self.assertIn("LangCode := 'uk'", script)

    def test_f8_overlay_state_is_localized(self):
        for language in ("ru", "uk", "en"):
            strings = app.UI_STRINGS[language]

            self.assertIn(
                "overlay_hotkey_on",
                strings,
            )
            self.assertIn(
                "overlay_hotkey_hidden",
                strings,
            )
            self.assertIn(
                "overlay_hotkey_off",
                strings,
            )

            self.assertIn(
                "F8",
                strings["overlay_hotkey_on"],
            )
            self.assertIn(
                "F8",
                strings["overlay_hotkey_hidden"],
            )
            self.assertIn(
                "F8",
                strings["overlay_hotkey_off"],
            )

    def test_windows_build_uses_runtime_elevation(self):
        root = Path(__file__).resolve().parents[1]

        app_source = (
            root / "app.py"
        ).read_text(encoding="utf-8")

        stable_workflow = (
            root
            / ".github"
            / "workflows"
            / "build-windows.yml"
        ).read_text(encoding="utf-8")

        rc_workflow = (
            root
            / ".github"
            / "workflows"
            / "build-release-candidate.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "def ensure_elevated_windows()",
            app_source,
        )
        self.assertIn(
            "IsUserAnAdmin",
            app_source,
        )
        self.assertIn(
            '"runas"',
            app_source,
        )
        self.assertIn(
            "if not ensure_elevated_windows():",
            app_source,
        )

        self.assertNotIn(
            "--uac-admin",
            stable_workflow,
        )
        self.assertNotIn(
            "--uac-admin",
            rc_workflow,
        )


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
