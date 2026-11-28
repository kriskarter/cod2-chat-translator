"""Dispatch native shell messages without touching the desktop or opening a menu."""
import ctypes
from ctypes import wintypes
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
pytest.importorskip("PySide6")
from qt_experiment.tray import WindowTray


def test_shell_callbacks_are_scoped_and_only_clicks_activate(monkeypatch):
    actions=[]
    from qt_experiment import tray
    monkeypatch.setattr(tray,"QTimer",SimpleNamespace(singleShot=lambda delay,fn:actions.append(fn)))
    target=SimpleNamespace(hwnd=123,callback=0x808f,restart=0xc123,
                           icon=Mock(),restore=Mock(),popup=Mock())
    target.icon.data.uID=7289
    def dispatch(event, hwnd=123):
        message=wintypes.MSG()
        message.hWnd=hwnd
        message.message=target.callback
        message.wParam=7289
        message.lParam=event
        return WindowTray.nativeEventFilter(target,b"windows_generic_MSG",ctypes.addressof(message))[0]
    assert not dispatch(0x402)  # balloon shown
    assert not dispatch(0x405,456)
    assert not actions
    for event in (0x203,0x405,0x205):
        assert dispatch(event)
        actions.pop()()
    assert [c.args for c in target.restore.call_args_list]==[(),(True,)]
    target.popup.assert_called_once()


@pytest.mark.skipif(__import__("os").name != "nt", reason="native Windows Qt dispatcher")
def test_win32_posted_tray_gestures_and_single_instance(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    # A separate process explicitly selects the Windows QPA plugin. Post only
    # private shell messages to our own hidden test HWND, never OS input.
    code = r"""
import ctypes, sys
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import QElapsedTimer
from PySide6.QtGui import QWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from qt_experiment.instance import PreviewInstance
from qt_experiment.tray import WindowTray
app=QApplication([])
window=QWindow()
window.create()
first=PreviewInstance(Path(sys.argv[1]))
other=PreviewInstance(Path(sys.argv[1]))
assert first.acquire() and first.server.isListening(),first.server.errorString()
assert not other.acquire()
calls=[]
def wait(predicate):
    clock=QElapsedTimer(); clock.start()
    while not predicate() and clock.elapsed()<4000:
        QTest.qWait(20)
    assert predicate(),calls
wait(lambda:first.pending)
class Probe(WindowTray):
    def restore(self,friends=False): calls.append(("open",friends))
    def popup(self): calls.append(("menu",False))
tray=Probe(window,str)
try:
    post=ctypes.windll.user32.PostMessageW
    post.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    for event in (0x402,0x203,0x405,0x205):
        assert post(tray.hwnd,tray.callback,tray.icon.data.uID,event)
    wait(lambda:len(calls)>=3)
    assert calls==[("open",False),("open",True),("menu",False)],calls
finally:
    tray.close()
    window.destroy()
"""
    subprocess.run([sys.executable,"-c",code,str(tmp_path)],check=True,timeout=25,
                   cwd=Path(__file__).resolve().parents[1],env={**os.environ,"QT_QPA_PLATFORM":"windows"})
