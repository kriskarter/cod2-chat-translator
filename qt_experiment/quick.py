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
    from .font_setup import ensure_ui_font
    fonts_ready = ensure_ui_font(app)
    if "--screenshot" in sys.argv and not fonts_ready:
        print("Qt UI font missing Latin or Cyrillic glyphs; screenshot rejected",file=sys.stderr)
        return 4
    from PySide6.QtGui import QIcon
    from .common import ROOT
    app.setWindowIcon(QIcon(str(ROOT / "assets" / "app.ico")))
    if '--live-translation' in sys.argv:
        from .translation_runtime import TranslationState, read_translation_config
        config = Path(sys.argv[sys.argv.index('--config') + 1]) if '--config' in sys.argv else None
        exe = Path(sys.argv[sys.argv.index('--game-exe') + 1]) if '--game-exe' in sys.argv else None
        log = Path(sys.argv[sys.argv.index('--log') + 1]) if '--log' in sys.argv else None
        knowledge = Path(sys.argv[sys.argv.index('--knowledge-file') + 1]) if '--knowledge-file' in sys.argv else None
        values = read_translation_config(config)
        # Import the previous F9 language pair without modifying its file.
        if config:
            import json
            try:
                outgoing = json.loads(config.with_name("outgoing_chat.json").read_text(encoding="utf-8"))
                if isinstance(outgoing, dict):
                    for old, new in (("source_language","outgoing_source_language"),("target_language","outgoing_target_language"),("enabled","outgoing_enabled")):
                        if old in outgoing: values.setdefault(new, outgoing[old])
            except (OSError, ValueError): pass
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
    qml_warnings = []
    engine.warnings.connect(lambda items: qml_warnings.extend(item.toString() for item in items))
    engine.rootContext().setContextProperty('prototype', state)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name('ComponentGallery.qml' if '--gallery' in sys.argv else 'Home.qml'))))
    if not engine.rootObjects():
        if not state.demo: state.stop()
        return 1
    if not state.demo and state.translationAvailable and "--screenshot" not in sys.argv:
        state.attach_window(engine.rootObjects()[0])
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                fn = ctypes.windll.dwmapi.DwmSetWindowAttribute
                fn.argtypes = [wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
                fn.restype = ctypes.c_long
                dark = ctypes.c_int(1)
                hwnd = int(engine.rootObjects()[0].winId())
                if fn(hwnd,20,ctypes.byref(dark),ctypes.sizeof(dark)) != 0:
                    fn(hwnd,19,ctypes.byref(dark),ctypes.sizeof(dark))
            except (OSError,AttributeError):
                pass
    if not state.demo and state.translationAvailable:
        state.start()

    if "--verify-game-hotkeys" in sys.argv:
        # Installed EXE probe uses the real Win32 hook without sending keyboard input.
        from PySide6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        state.translationChanged.connect(lambda: loop.quit() if state.gameHotkeysReady else None)
        if not state.gameHotkeysReady:
            QTimer.singleShot(8000, loop.quit)
            loop.exec()
        ok = state.gameHotkeysReady
        engine.rootObjects()[0].close()
        state.stop()
        del engine
        return 0 if ok else 5

    if "--size" not in sys.argv and "--screenshot" not in sys.argv:
        window = engine.rootObjects()[0]
        area = app.primaryScreen().availableGeometry()
        window.resize(min(1536,max(840,area.width()-24)),min(864,max(460,area.height()-48)))
    if '--size' in sys.argv:
        width, height = map(int, sys.argv[sys.argv.index('--size') + 1].split('x'))
        engine.rootObjects()[0].resize(width, height)
    if '--page' in sys.argv:
        engine.rootObjects()[0].setProperty("activePage", sys.argv[sys.argv.index("--page") + 1])
    if '--ui-language' in sys.argv and not state.demo and state.translationAvailable:
        state.setUiLanguage(sys.argv[sys.argv.index("--ui-language") + 1])
    if '--screenshot' in sys.argv:
        app.processEvents()
        if "--dialog" in sys.argv:
            from PySide6.QtTest import QTest
            QTest.qWait(60)
            name = sys.argv[sys.argv.index("--dialog")+1]
            if name not in ("add_server_dialog","server_remove_dialog","history_clear_dialog","knowledge_clear_dialog","game_logging_dialog","friends_panel","update_install_dialog"):
                if not state.demo: state.stop()
                del engine
                return 3
            engine.rootObjects()[0].setProperty("evidenceDialog",name)
            QTest.qWait(120)
        window = engine.rootObjects()[0]
        saved = window.grabWindow().save(sys.argv[sys.argv.index('--screenshot') + 1])
        window.close()
        if not state.demo: state.stop()
        del engine
        return 0 if saved and not qml_warnings else 2
    code = app.exec()
    if not state.demo: state.stop()
    del engine
    return code


if __name__ == '__main__':
    raise SystemExit(main())
