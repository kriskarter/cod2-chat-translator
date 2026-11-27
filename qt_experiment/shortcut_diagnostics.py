"""Local rotating diagnostics for the three game shortcuts only."""
import ctypes
import logging
import os
import queue
import threading
import time
from ctypes import wintypes
from logging.handlers import RotatingFileHandler
from pathlib import Path

SHORTCUTS = {0x77: "f8", 0x78: "toggle_popup", 0x79: "screenshot"}
NAMES = {"f8": "F8", "toggle_popup": "F9", "screenshot": "F10"}


def elevated(pid):
    """TokenElevation only. Never request privilege adjustment or VM access."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    adv.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    token = wintypes.HANDLE()
    try:
        if handle and adv.OpenProcessToken(handle, 8, ctypes.byref(token)):
            flag, size = wintypes.DWORD(), wintypes.DWORD()
            if adv.GetTokenInformation(token, 20, ctypes.byref(flag), ctypes.sizeof(flag), ctypes.byref(size)):
                return str(bool(flag.value))
        return "unknown"
    finally:
        if token: kernel.CloseHandle(token)
        if handle: kernel.CloseHandle(handle)


def other_translators():
    import psutil
    return [(p.pid, p.info["name"]) for p in psutil.process_iter(["name"])
            if p.pid != os.getpid() and (p.info["name"] or "").lower().startswith("cod2chattranslator")]


class ShortcutDiagnostics:
    def __init__(self, directory):
        self.logger = logging.Logger("cod2.shortcuts")
        directory = Path(directory)
        self.path = None
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self.handler = RotatingFileHandler(directory / "game-hotkeys.log", maxBytes=131072,
                                               backupCount=1, encoding="utf-8")
            self.path = self.handler.baseFilename
        except OSError:
            self.handler = logging.NullHandler()
        self.handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        self.logger.addHandler(self.handler)
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.user.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user.GetAsyncKeyState.restype = ctypes.c_short
        self.down = set()
        self.heartbeat = time.monotonic()
        self.edges = queue.SimpleQueue()
        self.worker = threading.Thread(target=self._record_edges, daemon=True, name="ShortcutTrace")
        self.worker.start()
        self.write("start pid=%s elevated=%s other_translators=%s", os.getpid(), elevated(os.getpid()), other_translators())

    def _record_edges(self):
        while True:
            edge = self.edges.get()
            if edge is None:
                return
            stamp, vk, injected, accepted, enabled = edge
            self.write("native_hook t=%.3f key=%s injected=%s focus=%s f9_enabled=%s", stamp,
                       NAMES[SHORTCUTS[vk]], injected, accepted, enabled)

    def write(self, msg, *args):
        self.logger.info(msg, *args)

    def focus(self):
        from outgoing_send import foreground_process_name, _foreground_api
        user, _ = _foreground_api()
        hwnd = user.GetForegroundWindow()
        pid = wintypes.DWORD()
        if hwnd: user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return "exe=%s pid=%d elevated=%s" % (foreground_process_name() or "unknown", pid.value,
                                              elevated(pid.value) if pid.value else "unknown")

    def missed(self, keyboard, now):
        # Windows updates async state after the low-level hook returns. A consumed
        # F9 may never be visible here. Hook delivery is therefore primary.
        for vk, event in SHORTCUTS.items():
            if self.user.GetAsyncKeyState(vk) & 0x8000:
                if vk not in self.down:
                    self.down.add(vk)
                    if vk not in keyboard.shortcut_held and now - keyboard.shortcut_at.get(vk, 0) > .12:
                        yield event
            else:
                self.down.discard(vk)

    def close(self):
        self.edges.put(None)
        self.worker.join(1)
        self.write("stop")
        self.handler.close()
