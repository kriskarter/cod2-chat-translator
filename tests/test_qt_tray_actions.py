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
