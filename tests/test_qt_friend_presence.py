"""Presence evidence, real UDP rounds, persisted friend edits and QML interaction."""
from pathlib import Path
import json
import os
import socket
import threading
import time
from unittest.mock import patch, Mock

import pytest
from server_monitor import Snapshot, Player
from qt_experiment.friend_presence import PresenceTracker, friend_key, display_name, normalize_friends, rich_name

A="127.0.0.1:28960"
B="127.0.0.1:28961"

def snap(address, names=(), state="online"):
    return Snapshot(address=address,state=state,name="TEST fixture · Alpha" if address==A else "TEST fixture · Bravo",
                    map_name="Toujane",clients=len(names),max_clients=32,
                    players=tuple(Player(n,10,42) for n in names))

def test_presence_two_rounds_move_outage_and_duplicates():
    p=PresenceTracker()
    p.configure(["^2Medic","Ghost"],[A,B])
    assert all(row["state"]=="unknown" for row in p.rows())
    assert p.observe((snap(A),snap(B)))==[]
    assert all(row["state"]=="offline" for row in p.rows())
    assert p.observe((snap(A,["^1MEDIC"]),snap(B)))==[]
    events=p.observe((snap(A,["^1MEDIC"]),snap(B)))
    assert [(e.kind,e.new_address) for e in events]==[("join",A)]
    assert p.rows()[0]["richName"]==rich_name("^1MEDIC")
    assert p.observe((snap(A,["Medic"]),snap(B)))==[]
    assert p.observe((snap(A),snap(B,["medic"])))==[]
    events=p.observe((snap(A),snap(B,["medic"])))
    assert [(e.kind,e.old_address,e.new_address) for e in events]==[("move",A,B)]
    assert p.observe((snap(A),snap(B,state="offline")))==[]
    assert p.rows()[0]["state"]=="unknown"
    assert p.observe((snap(A),snap(B,["^3Medic"])))==[]
    assert p.observe((snap(A),snap(B,["Medic"])))==[]
    assert p.observe((snap(A),snap(B)))==[]
    events=p.observe((snap(A),snap(B)))
    assert [(e.kind,e.old_address) for e in events]==[("leave",B)]
    assert p.observe((snap(A),snap(B)))==[]
    assert p.observe((snap(A,["Medic"]),snap(B,["^2MEDIC"])))==[]
    assert len([r for r in p.rows() if r["ambiguous"]])==2
    events=p.observe((snap(A,["Medic"]),snap(B,["^2MEDIC"])))
    assert {e.kind for e in events}=={"join"}
    assert p.observe((snap(A,["Medic"]),snap(B)))==[]
    assert all(e.kind!="move" for e in p.observe((snap(A,["Medic"]),snap(B))))
    # A permanently unreachable B cannot suppress observed changes on A.
    assert p.observe((snap(A),snap(B,state="limited")))==[]
    assert [e.kind for e in p.observe((snap(A),snap(B,state="limited")))]==["leave"]
    assert all(r["state"]=="unknown" for r in p.rows())

@pytest.mark.parametrize("first_half",["leave","join"])
def test_move_straddling_sequential_poll_rounds(first_half):
    tracker=PresenceTracker();tracker.configure(["Medic"],[A,B])
    assert tracker.observe((snap(A,["Medic"]),snap(B)))==[]
    intermediate=(snap(A),snap(B)) if first_half=="leave" else (snap(A,["Medic"]),snap(B,["Medic"]))
    assert tracker.observe(intermediate)==[]
    final=(snap(A),snap(B,["Medic"]))
    assert tracker.observe(final)==[]
    events=tracker.observe(final)
    assert [(e.kind,e.old_address,e.new_address) for e in events]==[("move",A,B)]
    assert tracker.observe(final)==[]

def test_duplicate_on_same_server_never_claims_move():
    tracker=PresenceTracker();tracker.configure(["Medic"],[A,B])
    tracker.observe((snap(A,["Medic","^2MEDIC"]),snap(B)))
    assert len(tracker.rows())==2 and all(r["ambiguous"] for r in tracker.rows())
    tracker.observe((snap(A),snap(B,["Medic"])))
    events=tracker.observe((snap(A),snap(B,["Medic"])))
    assert {e.kind for e in events}=={"join","leave"}

def test_nickname_markup_special_characters_and_collision():
    assert friend_key("^2MÉDIC")==friend_key("^1me\u0301dic")
    assert friend_key("A^^1")=="a^1"
    assert friend_key("A^1")=="a"
    assert display_name("^3A^^1<&")=="A^1<&"
    assert "&lt;&amp;" in rich_name("^3A^^1<&")
    assert normalize_friends(["^2Medic","^1MEDIC","A^^1","A^1","\x00bad"])==["^2Medic","A^^1","A^1"]

os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
os.environ.setdefault("QT_QUICK_BACKEND","software")
pytest.importorskip("PySide6")
from PySide6.QtCore import QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from qt_experiment.common import ROOT
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from qt_experiment.settings_store import SettingsStore
import knowledge_v2

def wait(app, predicate, seconds=5):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        app.processEvents()
        if predicate(): return True
        time.sleep(.01)
    return False

def find(item,name):
    if item.objectName()==name and item.isVisible(): return item
    for child in item.childItems():
        hit=find(child,name)
        if hit is not None: return hit
    return None

def screenshot(window,name):
    folder=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
    if folder:
        Path(folder).mkdir(parents=True,exist_ok=True)
        assert window.grabWindow().save(str(Path(folder)/(name+".png")))

def click(window,name,button=Qt.MouseButton.LeftButton):
    QTest.qWait(90)
    item=find(window.contentItem(),name)
    assert item is not None,name
    point=item.mapToScene(QPointF(item.width()/2,item.height()/2))
    assert 0<=point.x()<window.width() and 0<=point.y()<window.height(),(name,point)
    QTest.mouseClick(window,button,Qt.KeyboardModifier.NoModifier,QPoint(round(point.x()),round(point.y())))
    QTest.qWait(80)

def test_qml_stars_context_presence_and_persistence(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    source=tmp_path/"source.json"
    source.write_text(json.dumps({"server_monitor":{"servers":[{"address":A},{"address":B}]},"custom":"retain"}))
    original=source.read_bytes()
    store=SettingsStore(tmp_path/"qt.json")
    previous=knowledge_v2.RUNTIME
    cfg=read_translation_config(source)
    state=TranslationState(cfg,settings_store=store)
    engine=QQmlApplicationEngine()
    errors=[]
    engine.warnings.connect(lambda items:errors.extend(x.toString() for x in items))
    engine.rootContext().setContextProperty("prototype",state)
    from qt_experiment.font_setup import ensure_ui_font, font_has_ui_glyphs
    assert ensure_ui_font(app), "UI font missing Latin/Cyrillic glyphs"
    assert font_has_ui_glyphs(app.font())
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window=engine.rootObjects()[0]
    try:
        for s in (snap(A,["^2Medic","^1A^^1<&"]),snap(B)):
            state._apply_snapshot(s)
        state._apply_presence_round((snap(A,["^2Medic","^1A^^1<&"]),snap(B)))
        click(window,"friend_star_Medic")
        screenshot(window,"friends_roster_home")
        assert state.isFriend("MEDIC") and state.friendCount==1
        assert json.loads(store.path.read_text())["server_monitor"]["friends"]==["^2Medic"]
        click(window,"player_nick_Medic",Qt.MouseButton.RightButton)
        nick=find(window.contentItem(),"player_nick_Medic")
        menu=find(window.contentItem(),"context_copy_nick")
        p1=nick.mapToScene(QPointF(nick.width()/2,nick.height()/2));p2=menu.mapToScene(QPointF(menu.width()/2,menu.height()/2))
        assert abs(p1.x()-p2.x())<300 and abs(p1.y()-p2.y())<250,(p1,p2)
        screenshot(window,"friends_context_menu")
        click(window,"context_copy_nick")
        assert QGuiApplication.clipboard().text()=="Medic"
        click(window,"player_nick_Medic",Qt.MouseButton.RightButton)
        click(window,"context_copy_address")
        assert QGuiApplication.clipboard().text()==A
        click(window,"player_nick_A^1<&",Qt.MouseButton.RightButton)
        click(window,"context_add_friend")
        assert state.isFriend("A^^1<&")
        click(window,"friends_indicator")
        assert find(window.contentItem(),"friends_presence_list") is not None
        assert state.friendCount==2
        assert state.addFriend("Offline fixture")
        screenshot(window,"friends_panel_online_offline")
        state._apply_presence_round((snap(A,["^2Medic","^1A^^1<&"]),snap(B,state="limited")))
        screenshot(window,"friends_panel_unknown")
        state._apply_presence_round((snap(A,["^2Medic","^1A^^1<&"]),snap(B)))
        assert state.removeFriend("Offline fixture")
        QTest.keyClick(window,Qt.Key.Key_Escape)
        window.setProperty("activePage","servers")
        QTest.qWait(120)
        click(window,"friend_star_Medic")
        assert not state.isFriend("medic")
        screenshot(window,"friends_roster_servers")
        click(window,"player_nick_A^1<&",Qt.MouseButton.RightButton)
        click(window,"context_remove_friend")
        assert not state.isFriend("A^^1<&")
        click(window,"friends_indicator")
        assert find(window.contentItem(),"friends_presence_list") is not None
        QTest.keyClick(window,Qt.Key.Key_Escape)
        assert state.addFriend("^6A^^1<&")
        assert state.setFriendNotification("sound",True)
        assert not state.setFriendNotification("invalid",True)
        state._can_connect=True;state._game_exe=Path("CoD2MP_s.exe")
        state.changed.emit()
        state._apply_presence_round((snap(A),snap(B,["^4A^^1<&"])))
        click(window,"friends_indicator")
        with patch("qt_experiment.live_monitor.launch_connect_command") as launch:
            click(window,"friend_connect")
            launch.assert_called_once_with(state._game_exe,B)
            assert not state.connectServer("other.example:28960")
        state.friendNotice.emit("TEST · Друг появился","TEST fixture · Alpha")
        QTest.qWait(100)
        assert find(window.contentItem(),"friend_notice") is not None
        screenshot(window,"friends_notice")
        assert original==source.read_bytes()
        assert not errors,errors
    finally:
        window.close();del engine;state.stop();knowledge_v2.configure(previous)
    recovered=TranslationState(SettingsStore(store.path).load(read_translation_config(source)),settings_store=SettingsStore(store.path))
    try:
        assert recovered.isFriend("a^^1<&")
        assert recovered.friendNotificationOptions["sound"]
        assert recovered.removeFriend("A^^1<&")
        assert json.loads(store.path.read_text())["server_monitor"]["friends"]==[]
        store.path.write_text('{"external":true}')
        assert not recovered.addFriend("Ghost")
        assert not recovered.isFriend("Ghost")
        assert recovered.friendSaveError
        assert json.loads(store.path.read_text())=={"external":True}
    finally:
        recovered.stop();knowledge_v2.configure(previous)

class UdpFixture:
    def __init__(self,label):
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1",0));self.socket.settimeout(.1)
        self.address=f"127.0.0.1:{self.socket.getsockname()[1]}"
        self.label=label;self.names=[];self.limited=False;self.queries=0;self.stop_event=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def run(self):
        while not self.stop_event.is_set():
            try: data,peer=self.socket.recvfrom(2048)
            except socket.timeout: continue
            except OSError: break
            if data not in (b"\xff\xff\xff\xffgetstatus",b"\xff\xff\xff\xffgetinfo"):continue
            self.queries+=1
            header="infoResponse" if self.limited else "statusResponse"
            body=header+"\n\\gamename\\Call of Duty 2\\sv_hostname\\"+self.label+"\\mapname\\toujane\\sv_maxclients\\32\n"
            if not self.limited:body+="".join('10 42 "'+n+'"\n' for n in self.names)
            try:self.socket.sendto(b"\xff\xff\xff\xff"+body.encode("cp1252"),peer)
            except OSError:break
    def close(self):
        self.stop_event.set();self.socket.close();self.thread.join(1)

def test_background_two_real_udp_servers_and_options(tmp_path):
    app=QGuiApplication.instance() or QGuiApplication([])
    a,b=UdpFixture("Alpha"),UdpFixture("Bravo")
    previous=knowledge_v2.RUNTIME
    cfg=read_translation_config(None)
    cfg.update(auto_detect_profile=False,server_monitor={"servers":[{"address":a.address},{"address":b.address}],"friends":["Medic"],"notify_friends":True})
    state=TranslationState(cfg,settings_store=SettingsStore(tmp_path/"qt.json"))
    rounds=[]
    state.round_received.connect(lambda items:rounds.append(items))
    state._notifier=Mock()
    state._play_friend_sound=Mock()
    engine=QQmlApplicationEngine()
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window=engine.rootObjects()[0]
    window.showMinimized();app.processEvents()
    state.start()
    def poll():
        count=len(rounds);state.request("refresh")
        assert wait(app,lambda:len(rounds)>count)
    try:
        assert wait(app,lambda:len(rounds)>=1)
        assert state.friendRows[0]["state"]=="offline"
        a.names=["^2Medic"]
        poll();assert not state.notifications
        poll();assert len(state.notifications)==1
        assert state.friendRows[0]["address"]==a.address
        state._notifier.show.assert_called_once()
        assert state._notifier.show.call_args.kwargs["sound"] is False
        a.names=[];b.names=["MEDIC"]
        poll();poll()
        assert len(state.notifications)==2 and "→" in state.notifications[0]
        assert state.friendRows[0]["address"]==b.address
        b.limited=True;poll();assert state.friendRows[0]["state"]=="unknown"
        b.limited=False;poll();poll();assert len(state.notifications)==2
        assert state.setFriendNotification("leave",False)
        b.names=[];poll();poll()
        assert len(state.notifications)==2
        assert state.friendRows[0]["state"]=="offline"
        assert state.setFriendNotification("sound",True)
        a.names=["Medic"];poll();poll()
        assert len(state.notifications)==3
        assert state._notifier.show.call_args.kwargs["sound"] is False
        state._play_friend_sound.assert_called_once()
        poll();assert len(state.notifications)==3
        assert a.queries==b.queries==len(rounds)
    finally:
        window.close();del engine;state.stop();a.close();b.close();knowledge_v2.configure(previous)
