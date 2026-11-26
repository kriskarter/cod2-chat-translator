"""Windows shell notification for newly observed favorite nicknames."""
from __future__ import annotations
import os


class FriendNotice:
    def __init__(self, hwnd: int):
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
        self.data.uFlags=0x2|0x4
        self.data.szTip="CoD2 Chat Translator"
        self.data.hIcon=ctypes.windll.user32.LoadIconW(None,ctypes.c_void_p(32516))
        self.shell=ctypes.windll.shell32.Shell_NotifyIconW
        self.shell.argtypes=[wintypes.DWORD,ctypes.POINTER(Data)]
        self.active=bool(self.shell(0,ctypes.byref(self.data)))

    def show(self,title: str,body: str,*,sound: bool=True):
        if not self.active:return
        self.data.szInfoTitle=title[:63]
        self.data.szInfo=body[:255]
        self.data.dwInfoFlags=1 if sound else 1|0x10
        self.data.uFlags=0x2|0x4|0x10
        self.shell(1,self.ctypes.byref(self.data))

    def close(self):
        if self.active:
            self.shell(2,self.ctypes.byref(self.data))
            self.active=False
