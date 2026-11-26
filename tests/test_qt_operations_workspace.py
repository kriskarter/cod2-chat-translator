"""Qt preview: navigation, settings isolation, language and actual profile/HUD data."""
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
from qt_experiment.ui_text import translate
import knowledge_v2

def test_operations_and_localization(tmp_path):
    app = QGuiApplication.instance() or QGuiApplication([])
    store = SettingsStore(tmp_path / "qt.json")
    config = read_translation_config(None)
    config["server_monitor"] = {"servers": []}
    previous = knowledge_v2.RUNTIME
    state = TranslationState(config, installed_knowledge=tmp_path / "knowledge.json", settings_store=store)
    engine = QQmlApplicationEngine()
    errors = []
    engine.warnings.connect(lambda warnings: errors.extend(w.toString() for w in warnings))
    engine.rootContext().setContextProperty("prototype", state)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    try:
        log = tmp_path / "main" / "console_mp.log"
        log.parent.mkdir()
        log.write_text("")
        state.setLogPath(str(log))
        assert state.renameProfile(str(log), "Fixture")
        state.setAutoProfile(False)
        state.setNotifyFriends(True)
        state.setPreference("original", True)
        state.setHudValue("font", 18)
        state.setKnowledgeEnabled(False)
        state.setUiLanguage("uk")
        assert translate("Главная", "uk") == "Головна"
        assert state.trText("Главная") == "Головна"
        state.saveSettings()
        saved = json.loads(store.path.read_text())
        assert saved["server_profiles"][0]["name"] == "Fixture"
        assert saved["auto_detect_profile"] is False
        assert saved["server_monitor"]["notify_friends"] is True
        assert saved["show_original"] is True and saved["overlay"]["font_size"] == 18
        assert saved["knowledge_v2_enabled"] is False
        assert saved["ui_language"] == "uk"
        for lang in ("ru", "uk", "en"):
            state.setUiLanguage(lang)
            for page in ("home","servers","settings","history","outgoing","profiles","knowledge","notifications","about","stats","overlay"):
                window.setProperty("activePage", page)
                for _ in range(3): app.processEvents()
                assert not window.grabWindow().isNull()
        assert not errors, errors
    finally:
        window.close()
        del engine
        state.stop()
        knowledge_v2.configure(previous)

def test_automatic_profile_keeps_first_message_and_notifications(tmp_path):
    from server_monitor import Snapshot, Player
    from app import _path_key
    app = QGuiApplication.instance() or QGuiApplication([])
    a, b = tmp_path / "a.log", tmp_path / "b.log"
    a.write_text("old")
    b.write_text("old")
    config = read_translation_config(None)
    config.update(server_profiles=[{"path":str(a),"name":"A"},{"path":str(b),"name":"B"}],
                  auto_detect_profile=True, server_monitor={"servers":[{"address":"127.0.0.1:28960"}],"friends":["Medic"],"notify_friends":True})
    previous = knowledge_v2.RUNTIME
    state = TranslationState(config, log_path=a)
    try:
        b.write_text("old\nPlayer: enemy behind us\n")
        state._poll_profiles()
        assert state.logPath == str(b.resolve())
        state._tailer._switch_path(b)
        assert state._tailer.position == 3
        addr = "127.0.0.1:28960"
        def snapshot(players=(), status="online"):
            state._apply_snapshot(Snapshot(address=addr, state=status, players=players))
        player = Player("^2Medic", 1, 42)
        snapshot()
        snapshot(status="offline")
        snapshot((player,))
        assert not state.notifications
        snapshot()
        snapshot((player,))
        assert len(state.notifications) == 1
        snapshot()
        snapshot((player,))
        assert len(state.notifications) == 1
    finally:
        state.stop()
        knowledge_v2.configure(previous)


def test_preview_channel_never_returns_stable_or_external_link():
    from qt_experiment.preview_updates import check_preview_release
    assets = [{"name":"CoD2ChatTranslator_QtPreview_Setup.exe"},{"name":"SHA256SUMS.txt"}]
    result = check_preview_release(lambda url: [
        {"tag_name":"v99.0","prerelease":False,"assets":assets},
        {"tag_name":"qt-preview-123456789abc","prerelease":True,"draft":True,"assets":assets},
        {"tag_name":"qt-preview-abcdef123456","prerelease":True,"assets":assets,"html_url":"https://example.org"}
    ])
    assert result == {"tag":"qt-preview-abcdef123456","url":"https://github.com/kriskarter/cod2-chat-translator/releases/tag/qt-preview-abcdef123456"}
