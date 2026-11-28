"""Actual scene geometry + hit testing; no screenshots-as-assertions."""
import os
from pathlib import Path
import pytest
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ.setdefault("QT_QUICK_BACKEND","software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QObject, QPointF, QUrl
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
            for width,height in ((1366,768),(1342,672),(1536,864),(1920,1080),(900,500)):
                window.resize(width,height);window.setProperty("activePage","home");QTest.qWait(60)
                for card, names in [("f8Card",("f8Key","f8Switch","f8Language","f8HudButton")),("f9Card",("f9Key","f9Switch","f9Language","f9Target","f9HudButton"))]:
                    parent=find_visible(content,card)
                    assert parent is not None
                    inside(parent,content)
                    for name in names:
                        item=find_visible(content,name)
                        assert item is not None,name
                        inside(item,parent)
                        if name.endswith("HudButton"):
                            assert item.property("text")=={"ru":"Настроить","uk":"Налаштувати","en":"Configure"}[lang]
                            caption=item.findChild(QObject,"button_caption")
                            assert caption is not None and not caption.property("truncated"),(lang,width,height)
                banner=find_visible(content,"command_banner")
                panorama=find_visible(content,"command_panorama")
                assert panorama is not None
                assert bounds(panorama)==bounds(banner)
                source=panorama.property("sourceSize")
                painted_w,painted_h=panorama.property("paintedWidth"),panorama.property("paintedHeight")
                assert (source.width(),source.height())==(1534,198)
                assert painted_w>=banner.width()-1 and painted_h>=banner.height()-1
                assert abs(painted_w/painted_h-source.width()/source.height())<.03
                if (width,height) in ((1366,768),(1536,864),(1920,1080)):
                    assert abs(banner.height()-width*198/1534)<=1
                    assert abs(painted_h-banner.height())<=1
                for name in ("add_server_button","connect_button","home_roster","overlaySwitch"):
                    item=find_visible(content,name)
                    assert item is not None,name
                    inside(item,content)
                header=[bounds(find_visible(content,n)) for n in ("command_banner","command_panorama","command_navigation")]
                window.setProperty("activePage","settings");QTest.qWait(60)
                assert header==[bounds(find_visible(content,n)) for n in ("command_banner","command_panorama","command_navigation")]
                scroll=find_visible(content,"settings_scroll")
                scroll.setProperty("contentY",max(0,scroll.property("contentHeight")-scroll.height()))
                QTest.qWait(60)
                inside(find_visible(content,"settings_last"),scroll)
                save=find_visible(content,"save_settings")
                assert save is not None
                inside(save,find_visible(content,"translation_workspace"))
                window.setProperty("activePage","servers");QTest.qWait(60)
                inside(find_visible(content,"server_save"),find_visible(content,"server_workspace"))
                for name in ("server_add","server_refresh","server_connect"):
                    button=find_visible(content,name)
                    inside(button,find_visible(content,"server_workspace"))
                    assert bounds(button)[3] <= bounds(find_visible(content,"server_save"))[1]+1
                assert header==[bounds(find_visible(content,n)) for n in ("command_banner","command_panorama","command_navigation")]
                window.setProperty("activePage","outgoing");QTest.qWait(60)
                inside(find_visible(content,"save_settings"),find_visible(content,"translation_workspace"))
        assert not errors,errors
    finally:
        window.close();state.stop();del engine;knowledge_v2.configure(previous)

def test_panorama_is_exact_original_artwork():
    from PIL import Image, ImageChops
    approved=Image.open(ROOT/"docs/images/server_monitor_rc/reference.png").convert("RGB")
    panorama=Image.open(ROOT/"qt_experiment/reference_art/panorama.webp").convert("RGB")
    assert approved.size==(1536,864)
    assert panorama.size==(1534,198)
    assert ImageChops.difference(approved.crop((1,34,1535,232)),panorama).getbbox() is None


def test_about_links_and_localized_controls(tmp_path):
    from PySide6.QtCore import Slot
    from PySide6.QtGui import QDesktopServices

    class LinkRecorder(QObject):
        @Slot(QUrl)
        def receive(self, url):
            opened.append(url.toString())

    opened = []
    app = QGuiApplication.instance() or QGuiApplication([])
    receiver = LinkRecorder()
    previous = knowledge_v2.RUNTIME
    config = dict(read_translation_config(None), server_monitor={"servers":[]})
    state = TranslationState(config, settings_store=SettingsStore(tmp_path/"qt.json"))
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    window = engine.rootObjects()[0]
    base = "https://github.com/kriskarter/cod2-chat-translator"
    expected = [base,base+"/issues",base+"/blob/main/COPYRIGHT.md"]
    QDesktopServices.setUrlHandler("https",receiver,"receive")
    try:
        assert window.title() == "CoD2 Chat Translator — 1.22.0"
        window.setProperty("activePage","about")
        for language in ("en","ru","uk"):
            state.setUiLanguage(language)
            for width,height in ((1366,768),(1093,614),(911,512),(1536,864),(1229,691),
                                 (1024,576),(1920,1080),(1280,720)):
                window.resize(width,height)
                QTest.qWait(30)
                buttons = {obj.property("text"): obj for obj in window.findChildren(QObject)
                           if obj.metaObject().indexOfSignal("clicked()") >= 0 and obj.property("visible")}
                labels = ["★ "+state.trText("Поставить звезду на GitHub"),
                          state.trText("Сообщить об ошибке"),state.trText("Авторские права")]
                for label in labels:
                    button = buttons[label]
                    assert not button.findChild(QObject,"button_caption").property("truncated")
                    button.clicked.emit()
                assert opened[-3:] == expected
    finally:
        QDesktopServices.unsetUrlHandler("https")
        window.close()
        state.stop()
        del engine
        knowledge_v2.configure(previous)
