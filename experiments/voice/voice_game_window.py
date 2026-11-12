"""Win32 CoD2 borderless / overlay handling for the *isolated voice prototype*.

Important: Win32 TOPMOST cannot draw over exclusive fullscreen DirectX. The game
must first be switched to windowed rendering (/r_fullscreen 0; /vid_restart).
This module never sends keys to the game or alters its config.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

COD2_EXES = frozenset({"cod2mp_s.exe", "cod2mp.exe", "cod2_mp.exe"})
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU = 0x00080000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
SWP_NOOWNERZORDER = 0x0200
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
MONITOR_DEFAULTTONEAREST = 2
GA_ROOT = 2


def borderless_styles(style: int, exstyle: int) -> tuple[int, int]:
    """Pure style computation, independently unit-testable on Linux."""
    style = (int(style) & ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX
                            | WS_MAXIMIZEBOX | WS_SYSMENU)) | WS_POPUP | WS_VISIBLE
    exstyle = int(exstyle) & ~WS_EX_TOPMOST
    return style, exstyle


def overlay_styles(exstyle: int, click_through: bool) -> int:
    """Preserve Tk's own WS_EX_LAYERED; change only the relevant flags."""
    exstyle = int(exstyle) | WS_EX_TOOLWINDOW
    if click_through:
        return exstyle | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    return exstyle & ~(WS_EX_TRANSPARENT | WS_EX_NOACTIVATE)


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def _win32():
    if os.name != "nt":
        return None
    u = ctypes.WinDLL("user32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    fnptr = getattr(u, "GetWindowLongPtrW", None)
    setter = getattr(u, "SetWindowLongPtrW", None)
    if fnptr is None:
        fnptr = u.GetWindowLongW
        setter = u.SetWindowLongW
    fnptr.argtypes = [wintypes.HWND, ctypes.c_int]
    setter.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    fnptr.restype = ctypes.c_ssize_t
    setter.restype = ctypes.c_ssize_t
    u.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    u.EnumWindows.restype = wintypes.BOOL
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.IsWindowVisible.restype = wintypes.BOOL
    u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u.GetWindowTextLengthW.restype = ctypes.c_int
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowTextW.restype = ctypes.c_int
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
    u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                               ctypes.c_int, ctypes.c_int, wintypes.UINT]
    u.SetWindowPos.restype = wintypes.BOOL
    u.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    u.ShowWindow.restype = wintypes.BOOL
    u.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    u.MonitorFromWindow.restype = wintypes.HANDLE
    u.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
    u.GetMonitorInfoW.restype = wintypes.BOOL
    u.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    u.GetAncestor.restype = wintypes.HWND
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    k.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    k.QueryFullProcessImageNameW.restype = wintypes.BOOL
    return u, k, fnptr, setter


def find_cod2_window() -> int | None:
    api = _win32()
    if api is None:
        return None
    user32, kernel32, _, _ = api
    found: list[int] = []
    cbtype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return True
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return True
        name = ""
        try:
            size = wintypes.DWORD(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                name = os.path.basename(buf.value.replace("\\", "/")).lower()
        finally:
            kernel32.CloseHandle(handle)
        if name in COD2_EXES:
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cbtype(callback), 0)
    return found[0] if found else None


def _monitor_rect(user32, hwnd) -> tuple[int, int, int, int]:
    monitor = user32.MonitorFromWindow(wintypes.HWND(hwnd), MONITOR_DEFAULTTONEAREST)
    if not monitor:
        raise RuntimeError("Не найден монитор игрового окна")
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(info)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    r = info.rcMonitor
    return int(r.left), int(r.top), int(r.right - r.left), int(r.bottom - r.top)


def make_cod2_borderless(hwnd: int) -> tuple[bool, str]:
    """Resize a *windowed* CoD2 to borderless; never touch exclusive rendering."""
    api = _win32()
    if api is None or not hwnd:
        return False, "Не найдено окно CoD2"
    u, _, get_long, set_long = api
    h = wintypes.HWND(hwnd)
    try:
        style = int(get_long(h, GWL_STYLE))
        exstyle = int(get_long(h, GWL_EXSTYLE))
        if not (style & (WS_CAPTION | WS_THICKFRAME)):
            return False, ("Игра уже без рамки либо в exclusive fullscreen. "
                           "Если субтитры не видно, переключи CoD2 в оконный "
                           "режим: /r_fullscreen 0, затем /vid_restart.")
        left, top, width, height = _monitor_rect(u, hwnd)
        new_style, new_exstyle = borderless_styles(style, exstyle)
        # Validate before modifying any game window state.
        u.ShowWindow(h, SW_RESTORE)
        ctypes.set_last_error(0)
        old = set_long(h, GWL_STYLE, new_style)
        if not old and ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.set_last_error(0)
        old = set_long(h, GWL_EXSTYLE, new_exstyle)
        if not old and ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        if not u.SetWindowPos(h, wintypes.HWND(HWND_NOTOPMOST),
                              left, top, width, height,
                              SWP_FRAMECHANGED | SWP_SHOWWINDOW | SWP_NOOWNERZORDER):
            raise ctypes.WinError(ctypes.get_last_error())
        return True, f"CoD2: окно {width}×{height} без рамки"
    except Exception as exc:
        return False, f"Не удалось настроить окно игры: {exc}"


def _overlay_hwnd(win) -> tuple | None:
    api = _win32()
    if api is None:
        return None
    user32, _, get_long, set_long = api
    hwnd = int(win.winfo_id())
    # Tk may return a child HWND. Promote the actual top-level wrapper.
    top = user32.GetAncestor(wintypes.HWND(hwnd), GA_ROOT)
    return user32, get_long, set_long, wintypes.HWND(top or hwnd)


def configure_overlay(win, *, click_through: bool) -> bool:
    """Click-through when gaming; editable when moving subtitles."""
    api = _overlay_hwnd(win)
    if api is None:
        return False
    user32, get_long, set_long, hwnd = api
    current = int(get_long(hwnd, GWL_EXSTYLE))
    desired = overlay_styles(current, click_through)
    if current != desired:
        ctypes.set_last_error(0)
        previous = set_long(hwnd, GWL_EXSTYLE, desired)
        if not previous and ctypes.get_last_error():
            raise ctypes.WinError(ctypes.get_last_error())
        if not user32.SetWindowPos(hwnd, wintypes.HWND(HWND_TOPMOST),
                                   0, 0, 0, 0,
                                   SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED):
            raise ctypes.WinError(ctypes.get_last_error())
    return raise_overlay(win)


def raise_overlay(win) -> bool:
    api = _overlay_hwnd(win)
    if api is None:
        return False
    user32, _, _, hwnd = api
    return bool(user32.SetWindowPos(hwnd, wintypes.HWND(HWND_TOPMOST),
                0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE))
