"""End-to-end development runtime tests with real log parser and local engine."""
import os
import time
from pathlib import Path
from unittest.mock import patch
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
pytest.importorskip("PySide6")

from PySide6.QtCore import QUrl, QPointF, QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from app import ChatMessage
import knowledge_v2

ROOT = Path(__file__).resolve().parents[1]


def wait(app, predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(.02)
    return False


def click(window, name):
    def find(item):
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = find(child)
            if found is not None:
                return found
        return None
    item = find(window.contentItem())
    assert item is not None, name
    point = item.mapToScene(QPointF(item.width()/2, item.height()/2))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     QPoint(round(point.x()), round(point.y())))


def test_translation_full_log_to_qml_and_manual_outgoing(tmp_path):
    app = QGuiApplication.instance() or QGuiApplication([])
    log = tmp_path / "console_mp.log"
    log.write_bytes(b"Old^7: ^7enemy behind us\n")
    config = tmp_path / "config.json"
    config.write_text('{"server_monitor":{"servers":[]},"target_language":"ru"}')
    original = config.read_bytes()
    previous = knowledge_v2.RUNTIME
    state = TranslationState(read_translation_config(config), log_path=log)
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda warnings: errors.extend(w.toString() for w in warnings))
    engine.rootContext().setContextProperty("prototype", state)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    try:
        with patch("outgoing_chat.translate_with_google_fast", side_effect=AssertionError("unexpected network")) as google:
            state.start()
            assert wait(app, lambda: state._tailer.position == log.stat().st_size)
            assert not state.history
            with log.open("ab") as file:
                file.write(b"Player^7: ^7enemy behind us\n")
            assert wait(app, lambda: len(state.history) == 1)
            assert state.history[0]["nickname"] == "Player"
            assert state.history[0]["translated"] == "враг у нас за спиной"
            assert state.translationAvailable
            click(window, "nav_history")
            assert wait(app, lambda: window.property("activePage") == "history")
            assert not window.grabWindow().isNull()
            capture = os.environ.get("COD2_QT_TEST_SCREENSHOTS")
            if capture:
                assert window.grabWindow().save(str(Path(capture) / "translation_history.png"))
            click(window, "nav_settings")
            assert wait(app, lambda: window.property("activePage") == "settings")
            if capture:
                assert window.grabWindow().save(str(Path(capture) / "translation_settings.png"))
            click(window, "nav_home")
            assert wait(app, lambda: window.property("activePage") == "home")
            click(window, "manual_outgoing")
            assert wait(app, lambda: window.property("activePage") == "outgoing")
            state.submitOutgoing("ща зайду сзади", "ru", "en")
            assert wait(app, lambda: not state.outgoingBusy and bool(state.outgoingResult))
            assert state.outgoingResult == "i'll come around from behind"
            google.assert_not_called()
            if capture:
                assert window.grabWindow().save(str(Path(capture) / "translation_outgoing.png"))
            # Old results must not reappear after F8 stops or language changes.
            state.toggle("f8")
            state.ui_queue.put(("translation", ChatMessage("Stale", "test", epoch=0), "old", 1))
            state._drain()
            assert len(state.history) == 1
            assert config.read_bytes() == original
            assert not errors, errors
    finally:
        window.close()
        del engine
        state.stop()
        for worker in [state._tailer, *state._workers]:
            if worker.is_alive():
                worker.join(2)
        knowledge_v2.configure(previous)

def test_hud_lifecycle_and_expiry():
    from qt_experiment.native_hud import NativeHud
    from unittest.mock import Mock
    now = [10.0]
    surface = Mock()
    hud = NativeHud({"max_messages": 2, "message_ttl_seconds": 5}, factory=lambda: surface, clock=lambda: now[0])
    assert hud.enable(True)
    hud.add("A", "one", "один")
    hud.add("B", "two", "два")
    hud.add("C", "three", "три")
    assert [item.nickname for item in hud.items] == ["C", "B"]
    surface.render.assert_called()
    surface.show.assert_called()
    now[0] = 16
    hud.tick()
    assert not hud.items
    surface.hide.assert_called()
    hud.close()
    surface.destroy.assert_called_once()


@pytest.mark.skipif(os.name != "nt", reason="native HWND is Windows-only")
def test_real_windows_layered_surface():
    from qt_experiment.native_hud import NativeHud
    hud = NativeHud({"width": 320, "height": 100, "background_opacity": .2})
    try:
        assert hud.enable(True), hud.last_error
        hud.add("Test", "cover me", "прикрой меня")
        assert hud.enabled, hud.last_error
        assert hud.surface.hwnd
        assert hud.surface.image.size[0] == 320
        hud.clear()
    finally:
        hud.close()


def test_hud_fade_resets_on_new_message():
    from qt_experiment.native_hud import NativeHud
    from unittest.mock import Mock
    now = [0.]
    surface = Mock()
    hud = NativeHud({"message_ttl_seconds": 5, "fade_ms": 400, "fade_enabled": True}, factory=lambda: surface, clock=lambda: now[0])
    try:
        assert hud.enable(True)
        hud.add("A", "one", "один")
        now[0] = 4.8
        hud.tick()
        assert .45 < hud._alpha < .55
        surface.set_alpha.assert_called()
        hud.add("B", "two", "два")
        assert hud._alpha == 1.
    finally:
        hud.close()
