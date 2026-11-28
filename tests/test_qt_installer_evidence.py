"""Regression tests for installer process exit races, without a GUI."""
import subprocess
from unittest.mock import Mock

import psutil
import pytest

from tools import qt_installer_evidence as evidence


@pytest.mark.parametrize("where", ["constructor", "children"])
@pytest.mark.parametrize("code", [0, 5])
def test_exit_between_poll_and_children(monkeypatch, where, code):
    process = Mock(pid=4504)
    process.poll.side_effect = [None, code, code]
    parent = Mock()
    missing = psutil.NoSuchProcess(process.pid)
    factory = Mock(side_effect=missing) if where == "constructor" else Mock(return_value=parent)
    parent.children.side_effect = missing
    monkeypatch.setattr(evidence.psutil, "Process", factory)
    assert evidence.children_of(process) == []
    process.wait.assert_not_called()
    if code:
        with pytest.raises(RuntimeError, match="Wizard exit=5"):
            evidence.verify_exit(process, evidence.REQUIRED_CAPTURES)
    else:
        evidence.verify_exit(process, evidence.REQUIRED_CAPTURES)


def test_exit_handle_updates_after_pid_disappears(monkeypatch):
    process = Mock(pid=4504)
    process.poll.side_effect = [None, None, 0]
    process.wait.return_value = 0
    monkeypatch.setattr(evidence.psutil, "Process", Mock(side_effect=psutil.NoSuchProcess(4504)))
    assert evidence.children_of(process) == []
    process.wait.assert_called_once_with(timeout=1)
    evidence.verify_exit(process, evidence.REQUIRED_CAPTURES)


def test_missing_pid_with_live_handle_is_failure(monkeypatch):
    process = Mock(pid=4504)
    process.poll.return_value = None
    process.wait.side_effect = subprocess.TimeoutExpired("setup", 1)
    monkeypatch.setattr(evidence.psutil, "Process", Mock(side_effect=psutil.NoSuchProcess(4504)))
    with pytest.raises(psutil.NoSuchProcess):
        evidence.children_of(process)


def test_access_denied_is_not_suppressed(monkeypatch):
    process = Mock(pid=4504)
    process.poll.return_value = None
    monkeypatch.setattr(evidence.psutil, "Process", Mock(side_effect=psutil.AccessDenied(4504)))
    with pytest.raises(psutil.AccessDenied):
        evidence.children_of(process)


def test_cleanup_parent_disappears_between_poll_and_children(monkeypatch):
    process = Mock(pid=4504)
    process.poll.side_effect = [None, 0, 0]
    monkeypatch.setattr(evidence.psutil, "Process", Mock(side_effect=psutil.NoSuchProcess(4504)))
    evidence.stop_process_tree(process)
    process.terminate.assert_not_called()


def test_cleanup_child_disappears_after_enumeration(monkeypatch):
    process = Mock(pid=4504)
    process.poll.return_value = None
    child = Mock()
    child.terminate.side_effect = psutil.NoSuchProcess(4505)
    parent = Mock()
    parent.children.return_value = [child]
    monkeypatch.setattr(evidence.psutil, "Process", Mock(return_value=parent))
    evidence.stop_process_tree(process)
    child.terminate.assert_called_once()
    process.terminate.assert_called_once()


@pytest.mark.parametrize("code,seen", [(0, {"welcome","finish"}), (1, evidence.REQUIRED_CAPTURES), (None, evidence.REQUIRED_CAPTURES)])
def test_exit_and_all_three_captures_remain_mandatory(code, seen):
    process = Mock()
    process.poll.return_value = code
    with pytest.raises(RuntimeError, match="Wizard exit="):
        evidence.verify_exit(process, seen)
