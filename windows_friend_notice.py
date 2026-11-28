"""Windows shell notification for newly observed favorite nicknames."""
from __future__ import annotations
import os


class FriendNotice:
    def __init__(self, hwnd: int, *, icon_path=None, callback=0):
        self.active=False
        if os.name!="nt":return
        import ctypes
        from ctypes import wintypes
        self.ctypes=ctypes
        class Guid(ctypes.Structure):
            _fields_=[("Data1",wintypes.DWORD),("Data2",wintypes.WORD),
                      ("Data3",wintypes.WORD),("Data4",ctypes.c_ubyte*8)]
        class Data(ctypes.Structure):
            _fields_=[("cbSize",wintypes.DWORD),("hWnd",wintypes.HWND),
                      ("uID",wintypes.UINT),("uFlags",wintypes.UINT),
                      ("uCallbackMessage",wintypes.UINT),("hIcon",wintypes.HICON),
                      ("szTip",wintypes.WCHAR*128),("dwState",wintypes.DWORD),
                      ("dwStateMask",wintypes.DWORD),("szInfo",wintypes.WCHAR*256),
                      ("uTimeoutOrVersion",wintypes.UINT),
                      ("szInfoTitle",wintypes.WCHAR*64),("dwInfoFlags",wintypes.DWORD),
                      ("guidItem",Guid),("hBalloonIcon",wintypes.HICON)]
        self.data=Data()
        self.data.cbSize=ctypes.sizeof(Data)
        self.data.hWnd=hwnd
        self.data.uID=7289
        self.flags = 0x2 | 0x4 | bool(callback)
        self.data.uFlags=self.flags
        self.data.uCallbackMessage=callback
        self.data.szTip="CoD2 Chat Translator"
        self.owns_icon = False
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        if icon_path:
            load = self.user.LoadImageW
            load.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                             ctypes.c_int, ctypes.c_int, wintypes.UINT]
            load.restype = wintypes.HANDLE
            self.data.hIcon = load(None, str(icon_path), 1, 32, 32, 0x10)
            self.owns_icon = bool(self.data.hIcon)
        if not self.owns_icon:
            self.user.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
            self.user.LoadIconW.restype = wintypes.HICON
            self.data.hIcon = self.user.LoadIconW(None, ctypes.c_void_p(32516))
        self.shell=ctypes.windll.shell32.Shell_NotifyIconW
        self.shell.argtypes=[wintypes.DWORD,ctypes.POINTER(Data)]
        self.register()

    def register(self):
        self.data.uFlags = self.flags
        self.active = bool(self.shell(0, self.ctypes.byref(self.data)))

    def show(self,title: str,body: str,*,sound: bool=True):
        if not self.active:return False
        self.data.szInfoTitle=title[:63]
        self.data.szInfo=body[:255]
        self.data.dwInfoFlags=(4 if self.owns_icon else 1) | (0 if sound else 0x10)
        self.data.hBalloonIcon=self.data.hIcon if self.owns_icon else None
        self.data.uFlags=self.flags|0x10
        return bool(self.shell(1,self.ctypes.byref(self.data)))

    def close(self):
        if self.active:
            self.shell(2,self.ctypes.byref(self.data))
            self.active=False
        if getattr(self, "owns_icon", False):
            from ctypes import wintypes
            self.user.DestroyIcon.argtypes = [wintypes.HICON]
            self.user.DestroyIcon(self.data.hIcon)
            self.owns_icon = False
