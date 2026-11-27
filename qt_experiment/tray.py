"""Handle shell callbacks on Qt's native window. Only explicit clicks activate it."""
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMenu

from windows_friend_notice import FriendNotice
from .common import ROOT


class WindowTray(QAbstractNativeEventFilter):
    def __init__(self, window, translate):
        super().__init__()
        self.window = window
        self.translate = translate
        self.menu = None
        self.hwnd = int(window.winId())
        self.callback = 0x8000 + 143
        self.restart = ctypes.windll.user32.RegisterWindowMessageW("TaskbarCreated")
        self.icon = FriendNotice(self.hwnd, icon_path=ROOT / "assets/app.ico", callback=self.callback)
        QCoreApplication.instance().installNativeEventFilter(self)

    def restore(self, friends=False):
        if self.window.windowState() == Qt.WindowMinimized:
            self.window.showNormal()
        else:
            self.window.show()
        self.window.raise_()
        self.window.requestActivate()
        if friends:
            self.window.openFriendsFromTray()

    def popup(self):
        if self.menu:
            self.menu.close()
        self.menu = QMenu()
        self.menu.addAction(self.translate("Открыть окно"), lambda: self.restore())
        self.menu.addAction(self.translate("Друзья"), lambda: self.restore(True))
        self.menu.addSeparator()
        self.menu.addAction(self.translate("Выход"), QCoreApplication.quit)
        self.menu.popup(QCursor.pos())

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) != b"windows_generic_MSG" or not self.icon:
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        if msg.hWnd != self.hwnd:
            return False, 0
        if msg.message == self.restart:
            self.icon.register()
        elif msg.message == self.callback and msg.wParam == self.icon.data.uID:
            action = {0x203: self.restore, 0x405: lambda: self.restore(True),
                      0x205: self.popup, 0x7B: self.popup}.get(msg.lParam)
            if action:
                QTimer.singleShot(0, action)
                return True, 0
        return False, 0

    def show(self, title, detail, *, sound):
        return self.icon.show(title, detail, sound=sound)

    def close(self):
        if self.icon:
            QCoreApplication.instance().removeNativeEventFilter(self)
            self.icon.close()
            self.icon = None
        if self.menu:
            self.menu.close()
            self.menu = None
