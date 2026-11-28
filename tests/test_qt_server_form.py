"""Exercise the actual QML form and F9 settings with Qt click events, no game launch."""
import os
from pathlib import Path
import pytest

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ.setdefault("QT_QUICK_BACKEND","software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QUrl, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from qt_experiment.common import ROOT
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from qt_experiment.settings_store import SettingsStore


def test_actual_server_add_edit_and_f9_apply(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    cfg=read_translation_config(None)
    cfg.update(server_monitor={"servers":[]},auto_detect_profile=False,ui_language="ru")
    store=SettingsStore(tmp_path/"qt.json")
    state=TranslationState(cfg,settings_store=store)
    engine=QQmlApplicationEngine()
    warnings=[]
    engine.warnings.connect(lambda a:warnings.extend(x.toString() for x in a))
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window=engine.rootObjects()[0]
    window.resize(1342,672)
    def find(name):
        obj=window.findChild(QObject,name)
        assert obj is not None,name
        return obj
    def button(root,label):
        for obj in root.findChildren(QObject):
            if obj.property("text")==label and obj.metaObject().indexOfSignal("clicked()")>=0 and obj.property("visible"):
                return obj
        raise AssertionError(label)
    def click(item):
        point=item.mapToScene(QPointF(item.width()/2,item.height()/2))
        QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,QPoint(round(point.x()),round(point.y())))
        QTest.qWait(100)
    def capture(name):
        folder=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
        if folder:
            assert window.grabWindow().save(str(Path(folder)/name))
    try:
        window.setProperty("evidenceDialog","add_server_dialog")
        QTest.qWait(150)
        dialog=find("add_server_dialog")
        host=find("serverHostInput")
        port=find("serverPortInput")
        host.setProperty("text","148.251.139.73:12345")
        host.editingFinished.emit()
        QTest.qWait(60)
        assert host.property("text")=="148.251.139.73"
        assert port.property("text")=="12345"
        find("serverNameInput").setProperty("text","Massacre Extreme All Weapons TDM")
        capture("add_server_actual.png")
        click(button(dialog,"Добавить"))
        assert state.serverRecords[0]["address"]=="148.251.139.73:12345"
        # Reload from disk without invoking Save Settings.
        persisted=SettingsStore(store.path).load(cfg)["server_monitor"]["servers"]
        assert persisted == [{"address":"148.251.139.73:12345","label":"Massacre Extreme All Weapons TDM","favorite":False}]
        assert host.property("text")=="" and port.property("text")=="28960"
        window.setProperty("activePage","servers")
        QTest.qWait(150)
        find("editServerPort").setProperty("text","28961")
        click(button(find("server_workspace"),"Применить"))
        assert state.selected=="148.251.139.73:28961"
        capture("edit_server_actual.png")
        assert SettingsStore(store.path).load(cfg)["server_monitor"]["servers"][0]["address"]=="148.251.139.73:28961"
        window.setProperty("activePage","outgoing")
        QTest.qWait(100)
        window.setProperty("evidenceDialog","outgoing_hud_dialog")
        QTest.qWait(150)
        dlg=find("outgoing_hud_dialog")
        new=dict(state.outgoingHudSettings,width=850,height=250,x=42,y=90,font_size=18,background_opacity=.65)
        dlg.setProperty("draft",new)
        click(button(dlg,"Применить"))
        assert state.outgoingHudSettings["width"]==850
        assert state.outgoingHudSettings["background_opacity"]==.65
        assert SettingsStore(store.path).load(cfg)["outgoing_hud"]["x"]==42
        assert not warnings,warnings
    finally:
        window.close()
        del engine
        state.stop()
