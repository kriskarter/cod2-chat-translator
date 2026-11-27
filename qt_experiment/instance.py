"""One interactive Qt preview per user; a second launch raises the first window."""
import hashlib
from pathlib import Path
from PySide6.QtCore import QObject, QLockFile, Signal, QTimer, Qt
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class PreviewInstance(QObject):
    activated = Signal()

    def __init__(self, directory):
        super().__init__()
        directory = Path(directory)
        self.lock = QLockFile(str(directory / "interactive.lock"))
        self.lock.setStaleLockTime(0)
        self.name = "CoD2QtPreview-" + hashlib.sha256(str(directory.resolve()).casefold().encode()).hexdigest()[:20]
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.UserAccessOption)
        self.server.newConnection.connect(self._activate)
        self.pending = False

    def acquire(self):
        if not self.lock.tryLock(0):
            peer = QLocalSocket()
            peer.connectToServer(self.name)
            peer.waitForConnected(500)
            peer.disconnectFromServer()
            return False
        QLocalServer.removeServer(self.name)
        # Keep the first instance usable even when local IPC is unavailable.
        # The lock still prevents duplicate hooks and tray notifications.
        self.server.listen(self.name)
        return True

    def _activate(self):
        while self.server.hasPendingConnections():
            peer = self.server.nextPendingConnection()
            peer.close()
            peer.deleteLater()
        self.pending = True
        self.activated.emit()

    def bind(self, window):
        def restore():
            self.pending = False
            if window.windowState() == Qt.WindowMinimized:
                window.showNormal()
            window.raise_()
            window.requestActivate()
        self.activated.connect(restore)
        if self.pending:
            QTimer.singleShot(0, restore)
