"""Exercise the registered Windows callback and Qt drain without sending OS input."""
import ctypes
import os
import queue
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
pytest.importorskip("PySide6")


@pytest.mark.skipif(os.name != "nt", reason="Win32 callback ABI")
def test_registered_callback_delivers_scoped_shortcuts_and_no_plain_keys():
    from ctypes import wintypes
    from qt_experiment.game_controls import GameControls
    from qt_experiment.native_hud import NativeHud

    class Key(ctypes.Structure):
        _fields_ = [(n,wintypes.DWORD) for n in ("vk","scan","flags","stamp")]+[("extra",ctypes.c_size_t)]

    focused = [False]
    state = SimpleNamespace(record_sent=Mock(), show_f8_notice=Mock(), translationChanged=Mock(), f9=True, game_status=Mock(), toggle=Mock(), capture_game_screenshot=Mock(),
                            position_outgoing_hud=Mock())
    game = GameControls(state, {}, "ru","en",foreground=lambda:focused[0],
                        hud_factory=lambda cfg,orig:NativeHud(cfg,orig,factory=Mock))
    kb = game.keyboard
    kb.shortcut_trace = queue.SimpleQueue()
    try:
        kb.start()
        assert game.events.get(timeout=5)[0] == "hook_ready"
        def press(vk):
            data=Key(vk,0,0x10,0,0)
            for msg in (0x100,0x101):
                kb.callback(0,msg,ctypes.addressof(data))
        press(0x77)
        game.tick()
        state.toggle.assert_not_called()
        press(0x41)
        focused[0]=True
        for vk in (0x77,0x79,0x78): press(vk)
        game.tick()
        state.toggle.assert_called_once_with("f8")
        state.capture_game_screenshot.assert_called_once()
        assert game.active and game.last_shortcut=="F9"
        recorded=[kb.shortcut_trace.get_nowait()[1:4] for _ in range(4)]
        assert recorded==[(0x77,True,False),(0x77,True,True),(0x79,True,True),(0x78,True,True)]
        assert kb.shortcut_trace.empty()
    finally:
        game.close()
        kb._thread.join(5)


def test_poll_only_reads_three_keys_and_suppresses_seen_hook_edges():
    from qt_experiment.shortcut_diagnostics import ShortcutDiagnostics
    diag = ShortcutDiagnostics.__new__(ShortcutDiagnostics)
    down = {0x77,0x78,0x79}
    def read(vk):
        assert vk in (0x77,0x78,0x79)
        return 0x8000 if vk in down else 0
    diag.user = SimpleNamespace(GetAsyncKeyState=read)
    diag.down = set()
    kb = SimpleNamespace(shortcut_held={0x78},shortcut_at={0x79:99.99})
    assert list(diag.missed(kb,100)) == ["f8"]
    assert list(diag.missed(kb,101)) == []
    down.clear()
    assert list(diag.missed(kb,102)) == []
    down.add(0x79)
    assert list(diag.missed(kb,103)) == ["screenshot"]


def test_poll_runs_without_qt_ticks_and_stops_on_shutdown():
    import queue
    import threading
    import time
    from qt_experiment.shortcut_diagnostics import ShortcutDiagnostics
    diag=ShortcutDiagnostics.__new__(ShortcutDiagnostics)
    keys=set()
    diag.user=SimpleNamespace(GetAsyncKeyState=lambda code:0x8000 if code in keys else 0)
    diag.down=set()
    diag.poll_stop=threading.Event()
    diag.write=Mock()
    diag.focus=lambda:"game fixture"
    kb=SimpleNamespace(shortcut_held=set(),shortcut_at={})
    accepted=[True]
    events=queue.Queue()
    diag.start_polling(lambda:kb,lambda:accepted[0],events)
    try:
        keys.add(0x77)
        kind,(action,stamp)=events.get(timeout=2)
        assert (kind,action)==("poll_shortcut","f8") and stamp<=time.monotonic()
        time.sleep(.05)
        assert events.empty()
        keys.clear()
        time.sleep(.06)
        accepted[0]=False
        keys.add(0x79)
        time.sleep(.06)
        assert events.empty()
    finally:
        diag.poll_stop.set()
        diag.poll_thread.join(1)
    assert not diag.poll_thread.is_alive()


@pytest.mark.skipif(os.name != "nt", reason="Win32 sampling cost")
def test_native_poll_timer_runs_while_gui_is_idle(tmp_path):
    import json
    import queue
    import time
    from pathlib import Path
    import psutil
    from qt_experiment.shortcut_diagnostics import ShortcutDiagnostics
    diag = ShortcutDiagnostics(tmp_path)
    kb = SimpleNamespace(shortcut_held=set(),shortcut_at={})
    ticks=[]
    def keyboard():
        ticks.append(time.monotonic())
        return kb
    process=psutil.Process()
    process.cpu_percent()
    diag.start_polling(keyboard,lambda:False,queue.Queue())
    try:
        time.sleep(1.5)
    finally:
        diag.close()
    cpu=process.cpu_percent()
    assert len(ticks)>=10 and not diag.poll_thread.is_alive()
    gaps=sorted((b-a)*1000 for a,b in zip(ticks,ticks[1:]))
    dest=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
    if dest:
        (Path(dest)/"native_poll.json").write_text(json.dumps({
            "samples":len(ticks),"p95_interval_ms":round(gaps[int(len(gaps)*.95)],2),
            "process_cpu_pct":cpu,"rss_mib":round(process.memory_info().rss/2**20,1),
            "scenario":"Windows pytest process sleeping, isolated Win32 polling, no CoD2"
        },indent=2),encoding="utf-8")
