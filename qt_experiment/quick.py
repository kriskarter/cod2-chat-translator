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
        knowledge = config.with_name('knowledge_v2.json') if config else None
        state = TranslationState(read_translation_config(config), exe, log, knowledge)
        app.aboutToQuit.connect(state.stop)
        state.start()
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
    if '--size' in sys.argv:
        width, height = map(int, sys.argv[sys.argv.index('--size') + 1].split('x'))
        engine.rootObjects()[0].resize(width, height)
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
