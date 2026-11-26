"""Qt Quick candidate. Run: python -m qt_experiment.quick"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow  # register concrete QQuickWindow wrapper

from .common import PrototypeState, preview_state


def main():
    app = QGuiApplication(sys.argv)
    if '--live-translation' in sys.argv:
        from .translation_runtime import TranslationState, read_translation_config
        config = Path(sys.argv[sys.argv.index('--config') + 1]) if '--config' in sys.argv else None
        exe = Path(sys.argv[sys.argv.index('--game-exe') + 1]) if '--game-exe' in sys.argv else None
        log = Path(sys.argv[sys.argv.index('--log') + 1]) if '--log' in sys.argv else None
        knowledge = Path(sys.argv[sys.argv.index('--knowledge-file') + 1]) if '--knowledge-file' in sys.argv else None
        values = read_translation_config(config)
        if config is None:
            from app import installer_language_hint
            hint = installer_language_hint()
            if hint in ("ru", "uk", "en"): values["ui_language"] = hint
        store = None
        if "--settings-file" in sys.argv:
            from .settings_store import SettingsStore
            target = Path(sys.argv[sys.argv.index("--settings-file") + 1])
            if config and config.resolve() == target.resolve():
                raise ValueError("Qt settings file must differ from the imported Tk config")
            store = SettingsStore(target)
            try:
                hint = target.with_name("ui_language.txt").read_text(encoding="utf-8").strip()
                if not target.exists() and hint in ("ru", "uk", "en"): values["ui_language"] = hint
            except OSError: pass
            values = store.load(values)
        state = TranslationState(values, exe, log, knowledge, game_hotkeys="--game-hotkeys" in sys.argv, settings_store=store)
        app.aboutToQuit.connect(state.stop)
        state.start()
        if "--screenshot" not in sys.argv and not state.logPath:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, state.rescanProfiles)
    elif '--live-monitor' in sys.argv:
        from .live_monitor import LiveMonitorState, read_monitor_settings
        config = Path(sys.argv[sys.argv.index('--config') + 1]) if '--config' in sys.argv else None
        exe = Path(sys.argv[sys.argv.index('--game-exe') + 1]) if '--game-exe' in sys.argv else None
        state = LiveMonitorState(read_monitor_settings(config), exe)
        app.aboutToQuit.connect(state.stop)
        state.start()
    else:
        state = preview_state()
        state.action.connect(lambda name: print('Prototype action:', name, flush=True))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('prototype', state)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name('ComponentGallery.qml' if '--gallery' in sys.argv else 'Home.qml'))))
    if not engine.rootObjects():
        if not state.demo: state.stop()
        return 1
    if not state.demo and state.translationAvailable and "--screenshot" not in sys.argv:
        state.attach_window(engine.rootObjects()[0])
    if '--size' in sys.argv:
        width, height = map(int, sys.argv[sys.argv.index('--size') + 1].split('x'))
        engine.rootObjects()[0].resize(width, height)
    if '--page' in sys.argv:
        engine.rootObjects()[0].setProperty("activePage", sys.argv[sys.argv.index("--page") + 1])
    if '--ui-language' in sys.argv and not state.demo and state.translationAvailable:
        state.setUiLanguage(sys.argv[sys.argv.index("--ui-language") + 1])
    if '--screenshot' in sys.argv:
        app.processEvents()
        window = engine.rootObjects()[0]
        saved = window.grabWindow().save(sys.argv[sys.argv.index('--screenshot') + 1])
        window.close()
        if not state.demo: state.stop()
        del engine
        return 0 if saved else 2
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
