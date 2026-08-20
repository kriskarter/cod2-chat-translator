from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes


COD2_EXE_NAMES = {
    "cod2mp_s.exe",
    "cod2mp.exe",
    "cod2.exe",
}

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

SCAN_T = 0x14
SCAN_CTRL = 0x1D
SCAN_V = 0x2F
SCAN_ENTER = 0x1C


ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]


def foreground_process_name() -> str:
    if os.name != "nt":
        return ""

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    if not pid.value:
        return ""

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid.value,
    )

    if not handle:
        return ""

    try:
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)

        if not kernel32.QueryFullProcessImageNameW(
            handle,
            0,
            buf,
            ctypes.byref(size),
        ):
            return ""

        return os.path.basename(buf.value).casefold()

    finally:
        kernel32.CloseHandle(handle)


def is_cod2_foreground() -> bool:
    return foreground_process_name() in COD2_EXE_NAMES


def _open_clipboard(user32) -> bool:
    for _ in range(20):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.01)
    return False


def _get_clipboard_text() -> tuple[bool, str]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.GetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalLock.restype = ctypes.c_void_p

    if not _open_clipboard(user32):
        raise RuntimeError("Не удалось открыть буфер обмена")

    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return False, ""

        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return False, ""

        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return False, ""

        try:
            return True, ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)

    finally:
        user32.CloseClipboard()


def _set_clipboard_text(text: str) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.restype = ctypes.c_void_p

    raw = (text + "\0").encode("utf-16-le")

    handle = kernel32.GlobalAlloc(
        GMEM_MOVEABLE,
        len(raw),
    )

    if not handle:
        raise RuntimeError("GlobalAlloc clipboard failed")

    ptr = kernel32.GlobalLock(handle)
    if not ptr:
        kernel32.GlobalFree(handle)
        raise RuntimeError("GlobalLock clipboard failed")

    try:
        ctypes.memmove(ptr, raw, len(raw))
    finally:
        kernel32.GlobalUnlock(handle)

    if not _open_clipboard(user32):
        kernel32.GlobalFree(handle)
        raise RuntimeError("Не удалось открыть буфер обмена")

    try:
        if not user32.EmptyClipboard():
            kernel32.GlobalFree(handle)
            raise RuntimeError("EmptyClipboard failed")

        if not user32.SetClipboardData(
            CF_UNICODETEXT,
            handle,
        ):
            kernel32.GlobalFree(handle)
            raise RuntimeError("SetClipboardData failed")

        # После SetClipboardData владельцем handle становится Windows.
        handle = None

    finally:
        user32.CloseClipboard()


def _clear_clipboard() -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    if not _open_clipboard(user32):
        return

    try:
        user32.EmptyClipboard()
    finally:
        user32.CloseClipboard()


def _keyboard_input(scan: int, key_up: bool = False) -> INPUT:
    flags = KEYEVENTF_SCANCODE

    if key_up:
        flags |= KEYEVENTF_KEYUP

    return INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=0,
            wScan=scan,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        ),
    )


def _send_sequence(sequence: list[tuple[int, bool]]) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    user32.SendInput.argtypes = [
        wintypes.UINT,
        ctypes.POINTER(INPUT),
        ctypes.c_int,
    ]
    user32.SendInput.restype = wintypes.UINT

    inputs = [
        _keyboard_input(scan, key_up)
        for scan, key_up in sequence
    ]

    array_type = INPUT * len(inputs)
    array = array_type(*inputs)

    sent = user32.SendInput(
        len(inputs),
        array,
        ctypes.sizeof(INPUT),
    )

    if sent != len(inputs):
        raise RuntimeError(
            f"SendInput отправил {sent} из {len(inputs)} событий"
        )


def _tap(scan: int) -> None:
    _send_sequence([
        (scan, False),
        (scan, True),
    ])


def _paste() -> None:
    _send_sequence([
        (SCAN_CTRL, False),
        (SCAN_V, False),
        (SCAN_V, True),
        (SCAN_CTRL, True),
    ])


def send_cod2_chat_message(text: str) -> tuple[bool, str]:
    text = " ".join(str(text or "").split()).strip()

    if os.name != "nt":
        return False, "Отправка доступна только в Windows"

    if not text:
        return False, "Пустой перевод"

    if not is_cod2_foreground():
        return False, "CoD2 сейчас не является активным окном"

    had_previous_text = False
    previous_text = ""

    try:
        had_previous_text, previous_text = _get_clipboard_text()

        _set_clipboard_text(text)

        # Даём Windows обновить clipboard.
        time.sleep(0.06)

        if not is_cod2_foreground():
            return False, "Фокус ушёл с CoD2 — отправка отменена"

        # Физическая клавиша T — штатный чат всем.
        _tap(SCAN_T)
        time.sleep(0.10)

        # CoD2 у пользователя подтверждённо принимает Ctrl+V в чате.
        _paste()
        time.sleep(0.12)

        # Реальная отправка сообщения.
        _tap(SCAN_ENTER)
        time.sleep(0.10)

        return True, ""

    except Exception as exc:
        return False, str(exc)

    finally:
        # Возвращаем прежний текстовый clipboard.
        try:
            time.sleep(0.08)

            if had_previous_text:
                _set_clipboard_text(previous_text)
            else:
                _clear_clipboard()

        except Exception:
            pass
