"""Qt Quick candidate. Run: python -m qt_experiment.quick"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .common import PrototypeState, preview_state


def main():
    app = QGuiApplication(sys.argv)
    state = preview_state()
    state.action.connect(lambda name: print('Prototype action:', name, flush=True))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('prototype', state)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name('Home.qml'))))
    if not engine.rootObjects():
        return 1
    if '--size' in sys.argv:
        width, height = map(int, sys.argv[sys.argv.index('--size') + 1].split('x'))
        engine.rootObjects()[0].resize(width, height)
    if '--screenshot' in sys.argv:
        app.processEvents()
        window = engine.rootObjects()[0]
        window.screen().grabWindow(window.winId()).save(sys.argv[sys.argv.index('--screenshot') + 1])
        window.close()
        del engine
        return 0
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
