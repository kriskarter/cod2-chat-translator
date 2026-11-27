"""Explicit Windows elevation diagnostics and single-instance restart handoff."""
from __future__ import annotations
import os
import sys
import subprocess
import ctypes


def privilege_mismatch(own, game):
    """Unknown token states must not produce a false privilege warning."""
    return own == "False" and game == "True"


def game_privilege_status():
    if os.name != "nt":
        return False, False
    import psutil
    from outgoing_send import COD2_EXE_NAMES
    from .shortcut_diagnostics import elevated
    from ctypes import wintypes
    session = wintypes.DWORD()
    if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)):
        return False, False
    own = elevated(os.getpid())
    running, mismatch = False, False
    for proc in psutil.process_iter(["name"]):
        if (proc.info["name"] or "").casefold() not in COD2_EXE_NAMES:
            continue
        other_session = wintypes.DWORD()
        if not ctypes.windll.kernel32.ProcessIdToSessionId(proc.pid, ctypes.byref(other_session)) or other_session.value != session.value:
            continue
        running = True
        mismatch = mismatch or privilege_mismatch(own, elevated(proc.pid))
    return running, mismatch


def request_startup_elevation(prefer_admin, restarted=False):
    """Return (attempted, launched); no UI or worker has been created yet."""
    if restarted or os.name != "nt":
        return False, False
    from .shortcut_diagnostics import elevated
    if elevated(os.getpid()) != "False":
        return False, False
    if not prefer_admin and not game_privilege_status()[1]:
        return False, False
    launched, _ = restart_elevated()
    return True, launched


def restart_elevated():
    if os.name != "nt":
        return False, "Windows only"
    from ctypes import wintypes
    from .shortcut_diagnostics import elevated
    if elevated(os.getpid()) != "False":
        return False, "Already elevated or unknown"
    args = list(sys.argv[1:])
    if not getattr(sys, "frozen", False):
        args = ["-m", "qt_experiment.quick", *args]
    args += ["--restart-parent", str(os.getpid())]
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    execute = shell.ShellExecuteW
    execute.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR,
                        wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_int]
    execute.restype = ctypes.c_void_p
    result = execute(None, "runas", sys.executable, subprocess.list2cmdline(args), None, 1)
    return (True, "") if result and result > 32 else (False, str(result or 0))


def wait_for_parent(pid):
    if os.name != "nt" or pid <= 0 or pid == os.getpid():
        return False
    import psutil
    from .shortcut_diagnostics import elevated
    if elevated(os.getpid()) != "True":
        return False
    try:
        parent = psutil.Process(pid)
        parent.wait(timeout=20)
        return True
    except psutil.NoSuchProcess:
        return True
    except (psutil.TimeoutExpired, psutil.AccessDenied):
        return False
