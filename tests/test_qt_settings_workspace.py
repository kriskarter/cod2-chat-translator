"""Isolated Qt server/friend editing and opt-in settings persistence."""
import os
import json
from pathlib import Path
import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from qt_experiment.settings_store import SettingsStore
from qt_experiment.common import ROOT
import knowledge_v2


def test_server_workspace_and_explicit_save(tmp_path):
    app = QGuiApplication.instance() or QGuiApplication([])
    original = tmp_path / "config.json"
    original.write_text('{"server_monitor":{"servers":[]},"custom_key":"preserve"}')
    source_bytes = original.read_bytes()
    target = tmp_path / "qt_settings.json"
    store = SettingsStore(target)
    previous = knowledge_v2.RUNTIME
    state = TranslationState(store.load(read_translation_config(original)), settings_store=store)
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda warnings: errors.extend(w.toString() for w in warnings))
    engine.rootContext().setContextProperty("prototype", state)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    try:
        assert state.addServer("127.0.0.1:28960", "Local test")
        assert state.editServer("127.0.0.1:28960", "Renamed", True)
        assert state.rows[0]["favorite"]
        assert state.serverRecords[0]["label"] == "Renamed"
        assert state.editServerAddress("127.0.0.1:28960", "127.0.0.1:12345", "Renamed", True)
        assert state.selected == "127.0.0.1:12345"
        assert state.rows[0]["address"] == "127.0.0.1:12345"
        assert not state.editServerAddress("127.0.0.1:12345", "12345", "Bad", True)
        assert state.addServer("127.0.0.1:28960", "Second")
        assert not state.editServerAddress("127.0.0.1:12345", "127.0.0.1:28960", "Duplicate", True)
        assert state.removeServer("127.0.0.1:28960")
        from unittest.mock import patch
        state._can_connect = True
        state._game_exe = tmp_path/"CoD2MP_s.exe"
        with patch("qt_experiment.live_monitor.launch_connect_command") as launch:
            assert state.connectServer(state.selected)
            launch.assert_called_once_with(state._game_exe, "127.0.0.1:12345")
        assert state.addFriend("^2Medic")
        assert not state.addFriend("medic")
        window.setProperty("activePage", "servers")
        for _ in range(4):
            app.processEvents()
        assert not window.grabWindow().isNull()
        assert not errors, errors
        capture = os.environ.get("COD2_QT_TEST_SCREENSHOTS")
        if capture:
            assert window.grabWindow().save(str(Path(capture) / "server_workspace.png"))
        assert target.exists()
        auto_saved=json.loads(target.read_text(encoding="utf-8"))
        assert auto_saved["server_monitor"]["friends"] == ["^2Medic"]
        assert auto_saved["server_monitor"]["servers"] == [{"address":"127.0.0.1:12345","label":"Renamed","favorite":True}]
        state.setTargetLanguage("uk")
        state.saveSettings()
        saved = json.loads(target.read_text(encoding="utf-8"))
        assert saved["target_language"] == "uk"
        assert saved["server_monitor"]["servers"][0]["favorite"]
        assert saved["server_monitor"]["servers"][0]["address"] == "127.0.0.1:12345"
        assert saved["server_monitor"]["friends"] == ["^2Medic"]
        assert saved["custom_key"] == "preserve"
        assert original.read_bytes() == source_bytes
        assert state.removeServer("127.0.0.1:12345")
        state.removeFriend("medic")
        state.saveSettings()
        saved = json.loads(target.read_text(encoding="utf-8"))
        assert saved["server_monitor"]["servers"] == []
        assert saved["server_monitor"]["friends"] == []
        target.write_text('{"external":true}')
        assert not state.addServer("127.0.0.1:12345","Must not appear")
        assert not state.serverRecords
        assert "Ошибка сохранения" in state.serverSaveError
        state.saveSettings()
        assert json.loads(target.read_text()) == {"external": True}
        assert "Ошибка сохранения" in state.translationStatus
    finally:
        window.close()
        del engine
        state.stop()
        knowledge_v2.configure(previous)
