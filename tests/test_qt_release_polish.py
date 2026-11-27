"""Regression coverage for switching the actual Qt state and release UI."""
import base64
import os
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
pytest.importorskip("PySide6")
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from app import ChatMessage
from qt_experiment import windows_privileges
from qt_experiment.common import ROOT
from qt_experiment.game_controls import GameControls
from qt_experiment.native_hud import NativeHud
from qt_experiment.outgoing_hud import outgoing_config, render_editor
from qt_experiment.settings_store import SettingsStore
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from test_qt_game_controls import Keyboard


@pytest.fixture
def state(tmp_path):
    app = QGuiApplication.instance() or QGuiApplication([])
    cfg = read_translation_config(None)
    cfg["server_monitor"] = {"servers":[]}
    runtime = TranslationState(cfg,settings_store=SettingsStore(tmp_path/"qt.json"))
    runtime._hud = NativeHud(runtime._hud.config,factory=Mock)
    runtime._overlay = runtime._hud.enable(True)
    yield runtime
    runtime.stop()


def test_thirty_physical_edges_update_engine_and_hud(state):
    focused = [True]
    game = GameControls(state,{}, "ru","en",foreground=lambda:focused[0],keyboard_factory=Keyboard)
    state._game = game
    for index in range(30):
        stamp = time.monotonic()
        pair = [("f8",stamp), ("poll_shortcut",("f8",stamp))]
        for event in pair if index%2 else reversed(pair):
            game.events.put(event)
        epoch = state._chat_epoch
        state._drain()
        enabled = bool(index%2)
        assert state.f8 == state.enabled == state.overlay == state._hud.enabled == enabled
        assert state._chat_epoch == epoch+1
        for epoch_to_queue in (epoch,state._chat_epoch):
            state.ui_queue.put(("translation",ChatMessage("Medic",str(index),epoch=epoch_to_queue),"Cover me",5))
        state._drain()
        assert len(state._hud.items) == int(enabled)
        assert state.f9
        if enabled:
            assert state._hud.items[0].original==str(index)
        focused[0]=False
        game.events.put(("f8",None))
        state._drain()
        assert state.f8 == enabled
        focused[0]=True
    assert len(state.history)==15
    state.toggle("overlay")
    assert not state.f8 and not state.enabled and not state.overlay
    state.toggle("overlay")
    assert state.f8 and state.enabled and state.overlay


def test_late_uac_never_restarts_without_explicit_consent(state,monkeypatch):
    mismatch=[False]
    monkeypatch.setattr(windows_privileges,"game_privilege_status",lambda:(mismatch[0],mismatch[0]))
    request=Mock(return_value=(False,"5"))
    monkeypatch.setattr(windows_privileges,"restart_elevated",request)
    for value in (False,True,True,False,True):
        mismatch[0]=value
        state._check_game_privileges()
        QGuiApplication.processEvents()
        request.assert_not_called()
        assert state.gamePrivilegeMismatch == value
    state.restartElevated()
    request.assert_called_once()
    assert not state.alwaysAdmin
    assert state.gamePrivilegeMismatch


def test_saved_layout_and_smallest_compact_editor():
    assert outgoing_config({"width":430,"height":145})["mode"]=="expanded"
    cfg=outgoing_config(dict(mode="compact",width=200,height=60,font_size=9,auto_height=False))
    assert render_editor("длинное слово "*30,"cover me "*60,"Enter",cfg).size == (200,60)
    default=outgoing_config()
    assert (default["width"],default["height"],default["mode"])==(400,80,"compact")


def test_record_sent_and_export_session(state,tmp_path):
    state.record_sent("прикрой","cover me")
    row=state.history[0]
    assert row["direction"]=="out"
    state.setHistoryEnabled(False)
    state.record_sent("спасибо","thanks")
    assert len(state.history)==1
    path=tmp_path/"chat.txt"
    assert state.exportHistory(str(path))
    assert "прикрой\ncover me" in path.read_text(encoding="utf-8")
    assert not state.exportHistory(str(path))


def test_home_hud_buttons_and_warning(state):
    engine=QQmlApplicationEngine()
    warnings=[]
    engine.warnings.connect(lambda items:warnings.extend(x.toString() for x in items))
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    window=engine.rootObjects()[0]
    window.resize(1342,672)
    folder=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
    for key,name in (("f8","incoming"),("f9","outgoing")):
        button=window.findChild(QObject,key+"HudButton")
        QTest.qWait(60)
        assert button.property("text")=="Настроить"
        point=button.mapToScene(QPointF(button.width()/2,button.height()/2))
        QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,QPoint(round(point.x()),round(point.y())))
        QTest.qWait(150)
        dialog=window.findChild(QObject,name+"_hud_dialog")
        assert dialog.property("visible") and window.property("activePage")=="home"
        if folder: assert window.grabWindow().save(str(Path(folder)/(name+"_settings_home.png")))
        dialog.reject()
        QTest.qWait(80)
    state._privilege_mismatch=True
    state.translationChanged.emit()
    QTest.qWait(100)
    assert state.f8Status==state.f9Status=="Несовпадение прав"
    if folder:
        assert window.grabWindow().save(str(Path(folder)/"privileges_fixture.png"))
        for mode,height in (("compact",80),("expanded",160)):
            cfg=dict(state.outgoingHudSettings,mode=mode,height=height)
            data=state.outgoingHudPreview(cfg).split(",",1)[1]
            (Path(folder)/f"f9_{mode}_pixels.png").write_bytes(base64.b64decode(data))
    assert not warnings,warnings
    window.close()
    del engine


def test_f9_card_tracks_input_preview_send_cancel_and_focus(state):
    focused = [True]
    game = GameControls(state,{}, "ru","en",foreground=lambda:focused[0],keyboard_factory=Keyboard,
        hud_factory=lambda cfg, original: NativeHud(cfg,original,factory=Mock))
    state._game = game
    game.ready = True
    try:
        for _ in range(12):
            game.events.put(("toggle_popup",None))
            state._drain()
            assert state.f9 and state.f9Status == "Окно открыто"
            game.events.put(("cancel",None))
            state._drain()
            assert state.f9 and state.f9Status == "Ожидание игровой клавиши"
        game.events.put(("toggle_popup",None))
        state._drain()
        focused[0] = False
        state._drain()
        assert state.f9Status == "Ожидание игровой клавиши"
        focused[0] = True
        game.events.put(("toggle_popup",None))
        game.events.put(("text","test"))
        state._drain()
        assert state.f9Status == "Перевод…"
        game.pending = True
        game.events.put(("result",(game.generation,False,"test error")))
        state._drain()
        assert state.f9Status == "Ошибка"
        game.cancel()
        game.sending = True
        game.send_draft = "test"
        game.send_translation = "test"
        assert state.f9Status == "Отправка"
        game.events.put(("sent",(True,"")))
        state._drain()
        assert state.f9Status == "Сообщение отправлено"
        game.sent_until = time.monotonic()-1
        state._drain()
        assert state.f9 and state.f9Status == "Ожидание игровой клавиши"
    finally:
        game.close()
        state._game = None


def test_settings_backup_and_no_overwrite_after_external_edit(tmp_path):
    path = tmp_path/"settings.json"
    store = SettingsStore(path)
    initial = {"server_monitor":{"servers":[{"address":"148.251.139.73:12345"}]}}
    store.save(initial)
    store.save(dict(initial, ui_language="uk"))
    path.write_bytes(b"corrupt!")
    reopened = SettingsStore(path)
    assert reopened.load({}) == initial
    assert reopened.recovered
    assert path.read_bytes() == b"corrupt!"
    reopened.save(initial)
    assert SettingsStore(path).load({}) == initial
    path.write_bytes(b'{"external":true}')
    with pytest.raises(RuntimeError):
        reopened.save({})
    assert path.read_bytes() == b'{"external":true}'
