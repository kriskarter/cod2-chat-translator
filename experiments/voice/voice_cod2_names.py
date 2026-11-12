"""Experimental *read-only* player slot -> nickname map for CoD2 1.3 Win32.

CoD2x public reverse-engineering lists:
  clientInfo array 0x015CF994 (64 entries)
  struct clientInfo_t stride 0x4B8
  infoValid @ 0; nextValid @ 4; clientNum @ 8; name[32] @ 12
Sources:
  callofduty2x/CoD2x src/shared/cod2_client.h and cod2_player.h

These hard-coded offsets are NOT guaranteed for every CoD2 executable.
This feature is OFF by default and must be explicitly opted into. Opening
PROCESS_VM_READ may be flagged by some anti-cheat programs. Never modifies
game memory, never injects DLLs or intercepts gameplay.
"""
from __future__ import annotations

import ctypes
import os
import struct
from dataclasses import dataclass
from pathlib import Path

CLIENTINFO_BASE_13 = 0x015CF994
CLIENTINFO_STRIDE_13 = 0x04B8
CLIENTINFO_SLOTS = 64
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
COD2_NAMES = frozenset({"cod2mp_s.exe", "cod2mp.exe"})
MAX_RAW_NICK = 32


@dataclass(frozen=True)
class ClientInfoEvidence:
    slots: dict[int, str]
    state: str


def normalize_player_name(raw: bytes) -> str | None:
    """Names are CoD2 ANSI strings with optional color codes; never invent."""
    if b"\0" not in raw:
        return None
    value = raw.split(b"\0", 1)[0]
    if not (1 <= len(value) <= 31):
        return None
    if any(byte in (0x0A, 0x0D, 0x09) or byte < 0x20 for byte in value):
        return None
    try:
        name = value.decode("utf-8")
    except UnicodeDecodeError:
        name = value.decode("cp1251", errors="replace")
    name = name.strip()
    if not name or len(name) > MAX_RAW_NICK:
        return None
    return name


def extract_slot_names(memory: bytes) -> ClientInfoEvidence:
    expected = CLIENTINFO_STRIDE_13 * CLIENTINFO_SLOTS
    if len(memory) != expected:
        return ClientInfoEvidence({}, "wrong_memory_length")
    names = {}
    valid_count = 0
    inconsistent = 0
    for slot in range(CLIENTINFO_SLOTS):
        offset = slot * CLIENTINFO_STRIDE_13
        valid, next_valid, number = struct.unpack_from("<iii", memory, offset)
        if valid == 0:
            continue
        if valid != 1 or next_valid not in (0, 1) or number != slot:
            inconsistent += 1
            continue
        valid_count += 1
        name = normalize_player_name(memory[offset + 12:offset + 44])
        if name:
            names[slot] = name
    # No fabricated names from a foreign game version or a random memory page.
    if inconsistent > 3 or (valid_count and not names):
        return ClientInfoEvidence({}, "memory_layout_not_validated")
    if not names:
        return ClientInfoEvidence({}, "no_active_players")
    return ClientInfoEvidence(names, "coD2x_1_3_layout_validated")


def _read_process_bytes(pid: int) -> bytes:
    if os.name != "nt":
        raise OSError("Windows only")
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.ReadProcessMemory.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    k.ReadProcessMemory.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    handle = k.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION,
        False, pid,
    )
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        length = CLIENTINFO_STRIDE_13 * CLIENTINFO_SLOTS
        buffer = ctypes.create_string_buffer(length)
        actual = ctypes.c_size_t(0)
        if not k.ReadProcessMemory(
            handle, ctypes.c_void_p(CLIENTINFO_BASE_13),
            buffer, length, ctypes.byref(actual),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if actual.value != length:
            raise OSError("Incomplete read of CoD2 player-info table")
        return bytes(buffer.raw)
    finally:
        k.CloseHandle(handle)


def read_cod2_client_names(game_root: Path) -> ClientInfoEvidence:
    if os.name != "nt":
        return ClientInfoEvidence({}, "windows_only")
    import psutil
    try:
        target_dir = Path(game_root).resolve(strict=False)
        candidates = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            if (proc.info.get("name") or "").casefold() not in COD2_NAMES:
                continue
            exe = proc.info.get("exe")
            if not exe:
                continue
            if Path(exe).resolve(strict=False).parent != target_dir:
                continue
            candidates.append(proc.info["pid"])
        if len(candidates) != 1:
            return ClientInfoEvidence({}, (
                "game_not_found" if not candidates else "multiple_game_processes"
            ))
        memory = _read_process_bytes(candidates[0])
        return extract_slot_names(memory)
    except (psutil.Error, OSError, ValueError) as exc:
        return ClientInfoEvidence({}, "read_failed:" + type(exc).__name__)
