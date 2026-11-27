"""Qt preview UI evidence and measured event-loop latency on a fixture, not game FPS."""
import json, os, statistics, time
from pathlib import Path
import psutil
from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from qt_experiment.translation_runtime import TranslationState, read_translation_config
from qt_experiment.settings_store import SettingsStore
from qt_experiment.common import ROOT
from server_monitor import Snapshot, Player
from PySide6.QtTest import QTest

out=Path(os.environ.get("COD2_QT_AUDIT_DIR","/tmp/cod2-qt-final-audit"))
out.mkdir(parents=True,exist_ok=True)
cfg=read_translation_config(None)
cfg.update(auto_detect_profile=False,server_monitor={"servers":[],"friends":["Medic"]})
start=time.perf_counter()
app=QGuiApplication([])
state=TranslationState(cfg,settings_store=SettingsStore(out/"qt_settings.json"))
engine=QQmlApplicationEngine()
errors=[]
engine.warnings.connect(lambda items:errors.extend(x.toString() for x in items))
engine.rootContext().setContextProperty("prototype",state)
engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
assert engine.rootObjects()
window=engine.rootObjects()[0]
state.start()
app.processEvents()
assert not window.grabWindow().isNull()
print("first_frame_ms",round((time.perf_counter()-start)*1000),flush=True)
pages=("home","servers","settings","history","outgoing","profiles","knowledge","notifications","about","stats","overlay")
for lang in ("ru","uk","en"):
    state.setUiLanguage(lang)
    for w,h in ((1366,768),(1536,864),(1920,1080),(900,500)):
        window.resize(w,h)
        for page in pages:
            window.setProperty("activePage",page)
            for _ in range(3):app.processEvents()
            shot=window.grabWindow()
            assert not shot.isNull() and shot.width()==w and shot.height()==h,(w,h,page,shot.size())
            if lang=="ru" or (w,h)==(1366,768):
                assert shot.save(str(out/f"{lang}_{page}_{w}x{h}.png"))
    print("matrix",lang,"OK",flush=True)
window.setProperty("activePage","home");window.resize(1366,768);QTest.qWait(100)
# Fixture only: stop actual UDP worker before injecting an explicit local test snapshot.
state._monitor.stop()
state.addServer("127.0.0.1:28960","TEST fixture")
state._apply_snapshot(Snapshot(address="127.0.0.1:28960",state="online",name="TEST fixture — not a live server",map_name="Toujane",clients=10,max_clients=32,ping_ms=42,players=tuple(Player(n,10+i,p) for i,(n,p) in enumerate([("^2Medic",42),("^1Sniper",0),("^4KriS",None),("^6Ghost",170),("Scout",90),("Support",35),("Rifleman",56),("Observer",73),("Engineer",44),("Player 10",82)]))))
QTest.qWait(100);window.grabWindow().save(str(out/"home_roster_fixture.png"))
# Measure the existing roster and presence paths with local snapshots; no UDP traffic.
from PySide6.QtCore import QObject
from dataclasses import replace
roster=window.findChild(QObject, "roster_rows")
scroll_cost=[]; refresh_cost=[]
sample=Snapshot("127.0.0.1:28960",state="online",name="Test fixture",map_name="Toujane",
                clients=32,max_clients=32,ping_ms=42,players=tuple(Player("Player "+str(i),i,42) for i in range(32)))
for i in range(100):
    t=time.perf_counter()
    observation=replace(sample,ping_ms=40+i%5)
    state._apply_snapshot(observation);state._apply_presence_round((observation,))
    app.processEvents()
    refresh_cost.append((time.perf_counter()-t)*1000)
    t=time.perf_counter()
    roster.setProperty("contentY", float((i*7)%320))
    app.processEvents()
    scroll_cost.append((time.perf_counter()-t)*1000)
print("roster_scroll_p95_ms",round(sorted(scroll_cost)[94],2),"local_snapshot_and_friends_p95_ms",round(sorted(refresh_cost)[94],2),flush=True)
# Actual event loop lateness, not screenshot time. Warm up then sample 15s twice.
window.setProperty("activePage","home")
QTest.qWait(2000)
p=psutil.Process()
def measure(mode):
    loop=QEventLoop()
    timer=QTimer();timer.setInterval(50)
    samples=[];last=time.monotonic()
    def sample():
        nonlocal last
        now=time.monotonic();samples.append(max(0,(now-last)*1000-50));last=now
    timer.timeout.connect(sample)
    p.cpu_percent(None);timer.start();QTimer.singleShot(15000,loop.quit);loop.exec();timer.stop()
    print(mode, json.dumps({"cpu_pct":p.cpu_percent(None),"rss_mib":round(p.memory_info().rss/2**20,1),"timer_late_p50_ms":round(statistics.median(samples),2),"timer_late_p95_ms":round(sorted(samples)[int(len(samples)*.95)-1],2),"samples":len(samples)}),flush=True)
measure("idle_visible");window.showMinimized();QTest.qWait(1000);measure("idle_minimized")
window.close();state.stop();del window;del engine
print("warnings",json.dumps(errors,ensure_ascii=False),flush=True)
assert not errors,errors
