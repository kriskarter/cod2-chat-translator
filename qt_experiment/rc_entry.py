"""Isolated Qt Windows preview entry point. Stable configuration is read-only."""
from __future__ import annotations
import os
import sys
from pathlib import Path

def main():
    from app import config_path, installer_language_hint
    from qt_experiment.quick import main as quick_main
    stable = config_path()
    root = stable.parent.with_name("CoD2ChatTranslatorQtPreview")
    from qt_experiment.preview_updates import installed_build
    stable_profile = installed_build().get("channel") in ("stable", "candidate")
    if stable_profile:
        preview = root
        root = stable.parent
        if "--settings-file" not in sys.argv:
            from qt_experiment.stable_profile import migrate
            try:
                migrate(stable, preview)
            except (OSError, ValueError) as exc:
                from PySide6.QtWidgets import QApplication, QMessageBox
                app = QApplication.instance() or QApplication(sys.argv)
                QMessageBox.critical(None, "CoD2 Chat Translator", str(exc))
                return 7
    root.mkdir(parents=True, exist_ok=True)
    # Import stable configuration without migrating or overwriting it.
    if "--live-translation" not in sys.argv:
        sys.argv += ["--live-translation"]
    if not stable_profile and "--config" not in sys.argv and stable.is_file():
        sys.argv += ["--config", str(stable)]
    if "--settings-file" not in sys.argv:
        sys.argv += ["--settings-file", str(root / "qt_settings.json")]
    if "--knowledge-file" not in sys.argv:
        sys.argv += ["--knowledge-file", str(root / "knowledge_v2.json")]
    if "--game-hotkeys" not in sys.argv and os.name == "nt" and "--screenshot" not in sys.argv:
        sys.argv += ["--game-hotkeys"]
    return quick_main()

if __name__ == "__main__":
    raise SystemExit(main())
