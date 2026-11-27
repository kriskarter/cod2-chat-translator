"""Privilege checks and explicit restart without launching or elevating a process."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from qt_experiment import windows_privileges as win
from qt_experiment import shortcut_diagnostics


@pytest.mark.parametrize("own,game,expected", [
    ("False","True",True), ("True","True",False), ("False","False",False),
    ("True","False",False), ("unknown","True",False), ("False","unknown",False),
])
def test_mismatch(own, game, expected):
    assert win.privilege_mismatch(own, game) is expected


@pytest.mark.parametrize("result,expected", [(5,False),(0,False),(42,True)])
def test_explicit_uac_request_and_denial(monkeypatch, result, expected):
    execute = Mock(return_value=result)
    monkeypatch.setattr(win, "os", SimpleNamespace(name="nt", getpid=lambda:1234))
    monkeypatch.setattr(win, "sys", SimpleNamespace(argv=["qt.exe","--settings-file","C:/Qt Settings/qt.json"],
                                                  executable="C:/Qt Preview/qt.exe", frozen=True))
    monkeypatch.setattr(shortcut_diagnostics,"elevated",lambda pid:"False")
    monkeypatch.setattr(win.ctypes, "WinDLL", lambda *a,**kw:SimpleNamespace(ShellExecuteW=execute),raising=False)
    ok,_ = win.restart_elevated()
    assert ok is expected
    execute.assert_called_once()
    args=execute.call_args.args
    assert args[1]=="runas"
    assert args[2]=="C:/Qt Preview/qt.exe"
    assert "--restart-parent 1234" in args[3]
    assert '"C:/Qt Settings/qt.json"' in args[3]


def test_no_elevation_when_already_admin(monkeypatch):
    monkeypatch.setattr(win, "os", SimpleNamespace(name="nt", getpid=lambda:1234))
    monkeypatch.setattr(shortcut_diagnostics,"elevated",lambda pid:"True")
    execute=Mock()
    monkeypatch.setattr(win.ctypes,"WinDLL",execute,raising=False)
    assert not win.restart_elevated()[0]
    execute.assert_not_called()
