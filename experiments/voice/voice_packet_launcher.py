"""Opt-in, separate elevated Windows helper for *passive* CoD2 voice metadata.

The GUI never runs elevated. Windows UAC is requested by a direct user click.
Only this helper creates RAW IP sockets. It exits when the GUI closes or when
the user disables the probe. No packet contents, audio or usernames are saved.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProbeLaunch:
    ok: bool
    message: str


def launch_elevated_packet_probe(
    *,
    parent_pid: int,
    journal_path: Path,
    stop_path: Path,
) -> ProbeLaunch:
    if os.name != "nt":
        return ProbeLaunch(False, "Проба UDP доступна только в Windows")
    if parent_pid <= 0:
        return ProbeLaunch(False, "Некорректный PID основного приложения")
    # The only executable ever elevated is this same trusted local binary
    # (or sys.executable in a source-code development environment).
    script_args = []
    if not getattr(sys, "frozen", False):
        script_args.append(str(Path(__file__).with_name("voice_studio.py")))
    script_args.extend([
        "--cod2-voice-probe", "--parent-pid", str(parent_pid),
        "--journal", str(journal_path), "--stop-file", str(stop_path),
    ])
    arguments = subprocess.list2cmdline(script_args)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.ShellExecuteW.argtypes = [
        ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
        ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int,
    ]
    shell32.ShellExecuteW.restype = ctypes.c_void_p
    code = shell32.ShellExecuteW(
        None, "runas", str(Path(sys.executable).resolve()),
        arguments, None, 0,
    )
    if int(code or 0) <= 32:
        return ProbeLaunch(False, "Windows UAC отказан или запуск невозможен")
    return ProbeLaunch(True, "Сбор ID запущен. Ожидаю голосовые пакеты CoD2.")


def disable_probe(stop_path: Path) -> None:
    stop_path.parent.mkdir(parents=True, exist_ok=True)
    stop_path.write_text("stop", encoding="ascii")
