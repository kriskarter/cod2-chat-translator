"""Actual scene geometry + hit testing; no screenshots-as-assertions."""
import os
from pathlib import Path
import pytest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ.setdefault("QT_QUICK_BACKEND","software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QPointF, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from qt_experiment.settings_store import SettingsStore
from qt_experiment.common import ROOT
import knowledge_v2

def find_visible(item, name):
    if item.objectName()==name and item.isVisible(): return item
    for child in item.childItems():
        match=find_visible(child,name)
        if match is not None: return match
    return None

def bounds(item):
    a=item.mapToScene(QPointF(0,0))
    b=item.mapToScene(QPointF(item.width(),item.height()))
    return (a.x(),a.y(),b.x(),b.y())

def inside(item, container):
    a,b=bounds(item),bounds(container)
    assert a[0]>=b[0]-1 and a[1]>=b[1]-1 and a[2]<=b[2]+1 and a[3]<=b[3]+1,(item.objectName(),a,b)

def test_primary_controls_inside_cards_and_window(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    config=read_translation_config(None)
    config.update(server_monitor={"servers":[]},auto_detect_profile=False)
    previous=knowledge_v2.RUNTIME
    state=TranslationState(config,settings_store=SettingsStore(tmp_path/"qt.json"))
    from qt_experiment.font_setup import ensure_ui_font
    assert ensure_ui_font(app), "Missing UI font glyphs"
    engine=QQmlApplicationEngine()
    errors=[]
    engine.warnings.connect(lambda items:errors.extend(x.toString() for x in items))
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window=engine.rootObjects()[0]
    content=window.contentItem()
    try:
        for lang in ("ru","uk","en"):
            state.setUiLanguage(lang)
            for width,height in ((1366,768),(1536,864),(1920,1080),(900,500)):
                window.resize(width,height);window.setProperty("activePage","home");QTest.qWait(60)
                for card, names in [("f8Card",("f8Key","f8Switch","f8Language")),("f9Card",("f9Key","f9Switch","f9Language","f9Target","manual_outgoing"))]:
                    parent=find_visible(content,card)
                    assert parent is not None
                    inside(parent,content)
                    for name in names:
                        item=find_visible(content,name)
                        assert item is not None,name
                        inside(item,parent)
                for name in ("add_server_button","connect_button","home_roster","overlaySwitch"):
                    item=find_visible(content,name)
                    assert item is not None,name
                    inside(item,content)
                window.setProperty("activePage","settings");QTest.qWait(60)
                save=find_visible(content,"save_settings")
                assert save is not None
                inside(save,find_visible(content,"translation_workspace"))
                window.setProperty("activePage","servers");QTest.qWait(60)
                inside(find_visible(content,"server_save"),find_visible(content,"server_workspace"))
                window.setProperty("activePage","outgoing");QTest.qWait(60)
                inside(find_visible(content,"save_settings"),find_visible(content,"translation_workspace"))
        assert not errors,errors
    finally:
        window.close();state.stop();del engine;knowledge_v2.configure(previous)
