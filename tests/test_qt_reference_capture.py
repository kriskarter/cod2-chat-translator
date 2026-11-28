"""Compare actual QML geometry against the approved artwork using repeatable local data."""
import os
from pathlib import Path
from datetime import datetime, timezone

import pytest
pytest.importorskip("PySide6")
from PySide6.QtCore import QObject, QPointF, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from qt_experiment.common import ROOT
from qt_experiment.settings_store import SettingsStore
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from server_monitor import Snapshot, Player


def scene_item(parent, name):
    if parent.objectName() == name:
        return parent
    for child in parent.childItems():
        result = scene_item(child, name)
        if result is not None:
            return result


def capture(directory, output, check_geometry=True):
    app = QGuiApplication.instance() or QGuiApplication([])
    cfg = read_translation_config(None)
    names = ["Classic OBORONA", "Hardcore Frontline", "Old School Rifles"]
    addresses = [f"127.0.0.1:{28960+i}" for i in range(3)]
    servers = [dict(address=a, label=n, favorite=i<2) for i,(a,n) in enumerate(zip(addresses,names))]
    cfg.update(ui_language="ru", auto_detect_profile=False, server_monitor=dict(servers=servers, friends=["Sniper","Medic"]))
    state = TranslationState(cfg, settings_store=SettingsStore(directory/"settings.json"))
    state.setUiLanguage("ru")
    players = tuple(Player(n,s,p) for n,s,p in [("^3Sniper",36,40),("^4KriS",28,44),("^2Medic",21,56),("^6Ghost",17,61)])
    rounds = tuple(Snapshot(a, "online" if i<2 else "offline", names[i], ["Toujane","Carentan","Burgundy"][i],
                            clients=[24,12,0][i], max_clients=[32,24,20][i], ping_ms=[42,58,None][i],
                            players=players if i==0 else (), last_success=datetime.now(timezone.utc))
                   for i,a in enumerate(addresses))
    for snap in rounds: state._apply_snapshot(snap)
    state._apply_presence_round(rounds)
    state.select(addresses[0])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    window = engine.rootObjects()[0]
    try:
        window.resize(1536,830)
        QTest.qWait(100)
        shot = window.grabWindow()
        assert (shot.width(),shot.height()) == (1536,830)
        if output:
            output.mkdir(parents=True,exist_ok=True)
            assert shot.save(str(output/"reference_client_ru.png"))
            from tools.reference_comparison import comparison
            comparison(output/"reference_client_ru.png",output/"reference_components.png")
        if check_geometry:
            for name, target in {"command_banner":(0,0,1536,198), "command_navigation":(0,198,1536,50),
                                 "f8Card":(17,277,650,170),"f9Card":(17,468,650,170),
                                 "monitor_panel":(680,262,841,436),"system_bar":(287,712,1235,95)}.items():
                item=scene_item(window.contentItem(),name)
                pos=item.mapToScene(QPointF(0,0))
                actual=tuple(round(v) for v in (pos.x(),pos.y(),item.width(),item.height()))
                print(name, actual)
                assert max(abs(a-b) for a,b in zip(actual,target))<=5,(name,actual,target)

        if check_geometry:
            for address in addresses[1:]:
                state.removeServer(address)
            from dataclasses import replace
            full_roster = tuple(Player("Fixture "+str(i),i,None) for i in range(12))
            state._apply_snapshot(replace(rounds[0],players=full_roster))
            window.resize(1342,672)
            QTest.qWait(50)
            roster=scene_item(window.contentItem(),"roster_rows")
            print("laptop_roster_rows",roster.height()/25)
            assert roster.height() >= 150
            for page,control,is_list in (
                ("home", "f8Language", True), ("home","f9Target",True),
                ("settings","uiLocaleSelector",True),("settings","styleSelector",True),
                ("settings","logPathInput",False),("servers","serverLabelInput",False)):
                window.setProperty("activePage",page)
                QTest.qWait(45)
                item=scene_item(window.contentItem(),control)
                assert item and item.isVisible(),control
                item.forceActiveFocus()
                if is_list:
                    point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
                    QTest.mouseClick(window,Qt.LeftButton,Qt.NoModifier,point)
                    QTest.qWait(75)
                    popup=window.findChild(QObject,control+"_popup")
                    assert popup is not None and popup.property("opened"),control
                    QTest.keyClick(window,Qt.Key_Down)
                if output:
                    assert window.grabWindow().save(str(output/("owner_"+control+".png")))
                if is_list:
                    QTest.keyClick(window,Qt.Key_Escape)
                    QTest.qWait(40)
                    assert not popup.property("visible")
    finally:
        window.close()
        state.stop()
        del window,engine
        app.processEvents()


def test_reference_client_geometry(tmp_path):
    destination=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
    capture(tmp_path,Path(destination) if destination else None)
