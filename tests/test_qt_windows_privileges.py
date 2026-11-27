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


@pytest.mark.parametrize("preferred,restarted,own,mismatch,expected", [
    (True,False,"False",False,True),
    (False,False,"False",True,False),
    (False,False,"False",False,False),
    (True,True,"False",True,False),
    (True,False,"True",True,False),
])
def test_startup_uac_only_before_normal_initialization(monkeypatch, preferred, restarted, own, mismatch, expected):
    monkeypatch.setattr(win, "os", SimpleNamespace(name="nt",getpid=lambda:1234))
    monkeypatch.setattr(shortcut_diagnostics,"elevated",lambda pid:own)
    monkeypatch.setattr(win,"game_privilege_status",lambda:(mismatch,mismatch))
    request=Mock(return_value=(False,"5"))
    monkeypatch.setattr(win,"restart_elevated",request)
    assert win.request_startup_elevation(preferred,restarted) == (expected,False)
    assert request.call_count == int(expected)


@pytest.mark.parametrize("legacy", [{}, {"qt_always_admin":False}, {"qt_always_admin":True}])
def test_policy_migration_preserves_every_other_setting(tmp_path, legacy):
    from qt_experiment.admin_policy import persist_admin_policy, admin_policy
    from qt_experiment.settings_store import SettingsStore
    original=dict(legacy,server_monitor={"servers":[{"address":"148.251.139.73:12345",
        "label":"Massacre Extreme All Weapons TDM"}],"friends":["Medic"]},outgoing_hud={"width":430})
    store=SettingsStore(tmp_path/"qt.json")
    store.save(original)
    values,recovered=persist_admin_policy(store,{"ui_language":"uk",**original})
    assert values["qt_always_admin"] is True and values["qt_admin_policy_version"]==1
    assert not recovered
    assert store.load({})=={**original,"qt_always_admin":True,"qt_admin_policy_version":1}
    opted_out={**store.load({}),"qt_always_admin":False}
    store.save(opted_out)
    before=store.path.read_bytes()
    values,_=persist_admin_policy(SettingsStore(store.path),opted_out)
    assert values==opted_out and store.path.read_bytes()==before
    assert admin_policy(values)==values


def test_clean_policy_saved_before_elevation_without_importing_stable_data(tmp_path):
    from qt_experiment.admin_policy import persist_admin_policy
    from qt_experiment.settings_store import SettingsStore
    store=SettingsStore(tmp_path/"qt.json")
    original={"server_monitor":{"servers":[{"address":"127.0.0.1:12345"}]}}
    values,_=persist_admin_policy(store,original)
    assert values["server_monitor"]==original["server_monitor"]
    assert store.load({})=={"qt_always_admin":True,"qt_admin_policy_version":1}


def test_uac_acceptance_requests_only_one_restart(monkeypatch):
    monkeypatch.setattr(win,"os",SimpleNamespace(name="nt",getpid=lambda:1234))
    monkeypatch.setattr(shortcut_diagnostics,"elevated",lambda pid:"False")
    request=Mock(return_value=(True,""))
    monkeypatch.setattr(win,"restart_elevated",request)
    assert win.request_startup_elevation(True)==(True,True)
    assert win.request_startup_elevation(True,restarted=True)==(False,False)
    request.assert_called_once()
