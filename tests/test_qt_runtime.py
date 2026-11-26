"""Exercise the real QML engine and the existing UDP wire protocol locally."""
import os
import socket
import threading
import time
from pathlib import Path

import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
pytest.importorskip("PySide6")

from PySide6.QtCore import QPoint, QPointF, QUrl, Qt, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from qt_experiment.common import preview_state
from qt_experiment.live_monitor import LiveMonitorState, read_monitor_settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def app():
    instance = QGuiApplication.instance() or QGuiApplication([])
    yield instance


def load_window(app, state):
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("prototype", state)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    app.processEvents()
    return engine, window


def click(window, object_name):
    item = window.findChild(QQuickItem, object_name)
    assert item is not None, object_name
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     QPoint(round(point.x()), round(point.y())))


def test_quick_real_controls_and_geometry(app):
    state = preview_state()
    engine, window = load_window(app, state)
    try:
        for width, height in ((900,620),(1366,768),(1536,864),(1920,1080)):
            window.resize(width, height)
            app.processEvents()
            assert window.width() == width and window.height() == height
            assert not window.grabWindow().isNull()
        click(window, "f8Key")
        assert not state.f8
        click(window, "f8Switch")
        assert state.f8
        click(window, "overlaySwitch")
        assert not state.overlay
    finally:
        window.close()
        del engine


def test_live_udp_worker_delivers_to_qt_and_never_simulates_translation(app, tmp_path):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    server.settimeout(3)
    address = f"127.0.0.1:{server.getsockname()[1]}"
    config = tmp_path / "config.json"
    config.write_text('{"server_monitor":{"servers":[{"address":"' + address +
                      '","label":"Local fixture"}],"friends":["Medic"]}}')
    original = config.read_bytes()
    payload = (b"\xff\xff\xff\xffstatusResponse\n"
               b"\\gamename\\Call of Duty 2\\sv_hostname\\Local fixture\\mapname\\toujane\\sv_maxclients\\32\n"
               b'12 42 "^2Medic"\n')

    def answer():
        try:
            data, peer = server.recvfrom(1024)
            assert data == b"\xff\xff\xff\xffgetstatus"
            server.sendto(payload, peer)
        finally:
            server.close()

    thread = threading.Thread(target=answer, daemon=True)
    thread.start()
    state = LiveMonitorState(read_monitor_settings(config))
    state.start()
    try:
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and state.rows[0]["state"] != "online":
            app.processEvents()
            time.sleep(.01)
        assert state.rows[0]["state"] == "online"
        assert state.rows[0]["map"] == "toujane"
        assert state.players[0]["name"] == "Medic"
        assert state.friendCount == 1
        assert not state.demo and not state.f8 and not state.overlay
        state.toggle("f8")
        assert not state.f8
        assert not state.addServer(address, "Duplicate")
        assert config.read_bytes() == original
    finally:
        state.stop()
        thread.join(timeout=3)
