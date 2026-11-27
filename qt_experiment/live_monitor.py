"""Qt-thread bridge to the existing, unmodified UDP query engine.

This is intentionally a monitor-only development entry point, not the
translator RC. It never writes the existing Tk application's configuration.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from dataclasses import replace
from threading import Event

from PySide6.QtCore import Qt, Signal, Slot, Property
from server_monitor import Monitor, Snapshot, Server, MAX_SERVERS, canonical_address, load_settings, normalized_name, plain_name
from server_catalog import MULTIPLAYER_IMAGE_NAMES, launch_connect_command
from .common import PrototypeState, row_from_snapshot
from .friend_presence import PresenceTracker, friend_key, valid_friend, qt_monitor_settings


def read_monitor_settings(path: Path | None) -> dict:
    if path is None:
        return qt_monitor_settings({})
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration root must be an object")
    return qt_monitor_settings(raw.get("server_monitor", {}))


class LiveMonitorState(PrototypeState):
    snapshot_received = Signal(object)
    recordsChanged = Signal()
    round_received = Signal(object)

    def __init__(self, settings: dict, game_exe: Path | None = None):
        super().__init__(tuple(row_from_snapshot(Snapshot(address=s.address, name=s.label))
                               for s in settings["servers"]))
        self._demo = False
        self._status = "UDP: ожидание ответа"
        self._f8 = self._f9 = self._overlay = self._smart = False
        self._settings = settings
        self._friend_error = ""
        self._presence = PresenceTracker()
        self._presence.configure(settings["friends"],self._rows)
        self._game_exe = game_exe
        self._can_connect = bool(os.name == "nt" and game_exe and game_exe.is_file()
                                 and game_exe.name.casefold() in MULTIPLAYER_IMAGE_NAMES)
        self._closing = Event()
        self._monitor = Monitor(settings, self._on_worker_snapshot, round_callback=self._on_worker_round)
        self.snapshot_received.connect(self._apply_snapshot, Qt.ConnectionType.QueuedConnection)
        self.round_received.connect(self._apply_presence_round, Qt.ConnectionType.QueuedConnection)
        self.action.connect(self._dispatch)

    def _is_friend(self, name):
        return friend_key(name) in self._presence.friends

    def _is_favorite(self, address):
        return any(s.address == address and s.favorite for s in self._settings["servers"])

    @Property(bool, constant=True)
    def serverManagementAvailable(self): return True

    @Property('QVariantList', notify=recordsChanged)
    def serverRecords(self):
        return [dict(address=s.address, label=s.label, favorite=s.favorite) for s in self._settings["servers"]]

    @Property('QStringList', notify=recordsChanged)
    def friends(self):
        return list(self._settings["friends"])

    def _settings_changed(self):
        pass

    @Property("QVariantList", notify=PrototypeState.friendsChanged)
    def friendRows(self): return self._presence.rows()

    @Property(str, notify=PrototypeState.friendsChanged)
    def friendSaveError(self): return self._friend_error

    def _count_friends(self):
        count=len({friend_key(row["rawName"]) for row in self._presence.rows() if row["state"]=="online"})
        if count!=self._friend_count:
            self._friend_count=count
            self.changed.emit()

    def _save_friend_settings(self):
        # Monitor-only mode is intentionally session-only; installed Qt overrides.
        return True

    def _refresh_presence(self):
        self._presence.configure(self._settings["friends"],self._rows)
        self._count_friends()
        self.friendsChanged.emit()

    def _on_worker_round(self,snapshots):
        if not self._closing.is_set(): self.round_received.emit(snapshots)

    @Slot(object)
    def _apply_presence_round(self,snapshots):
        if self._closing.is_set() or {s.address for s in snapshots}!=set(self._rows):
            return
        labels={s.address:s.label for s in self._settings["servers"]}
        snapshots=tuple(replace(s,name=s.name or labels.get(s.address,"")) for s in snapshots)
        self._presence.configure(self._settings["friends"],self._rows)
        before=self._presence.rows()
        events=self._presence.observe(snapshots)
        self._count_friends()
        if before!=self._presence.rows(): self.friendsChanged.emit()
        for event in events: self._on_presence_event(event)

    def _on_presence_event(self,event): pass

    @Slot(str, str, bool, result=bool)
    def editServer(self, address, label, favorite):
        if address not in self._rows:
            return False
        self._monitor.replace_servers([replace(s, label=label.strip()[:80], favorite=favorite)
                                       if s.address == address else s for s in self._settings["servers"]])
        self._settings_changed()
        self.recordsChanged.emit()
        self.rowsChanged.emit()
        self.changed.emit()
        return True

    @Slot(str, result=bool)
    def removeServer(self, address):
        if address not in self._rows:
            return False
        self._monitor.replace_servers([s for s in self._settings["servers"] if s.address != address])
        self._rows.pop(address)
        self._presence.configure(self._settings["friends"],self._rows)
        self.friendsChanged.emit()
        if self._selected == address:
            self._selected = next(iter(self._rows), "")
        self._count_friends()
        self._settings_changed()
        self.recordsChanged.emit()
        self.rowsChanged.emit()
        self.changed.emit()
        return True

    def _replace_friends(self, values):
        old=self._settings["friends"]
        self._settings["friends"]=values
        self._friend_error=""
        if not self._save_friend_settings():
            self._settings["friends"]=old
            self.friendsChanged.emit()
            return False
        self._refresh_presence()
        self.recordsChanged.emit()
        self.changed.emit()
        return True

    @Slot(str, result=bool)
    def addFriend(self,name):
        name=valid_friend(name)
        if not name or len(self._settings["friends"])>=100 or self._is_friend(name):
            self._friend_error=self.trText("Некорректный никнейм, повтор или лимит друзей")
            self.friendsChanged.emit()
            return False
        return self._replace_friends([*self._settings["friends"],name])

    @Slot(str, result=bool)
    def removeFriend(self,name):
        if not self._is_friend(name): return False
        return self._replace_friends([f for f in self._settings["friends"] if friend_key(f)!=friend_key(name)])

    @Slot(str, result=bool)
    def toggleFriend(self,name):
        return self.removeFriend(name) if self._is_friend(name) else self.addFriend(name)

    @Slot(str, result=bool)
    def connectServer(self,address):
        if not self._can_connect or address not in self._rows:
            return False
        try:
            launch_connect_command(self._game_exe,address)
            self._status=self.trText("Запуск CoD2")
            self.changed.emit()
            return True
        except (OSError,ValueError) as error:
            self._status=self.trText("Ошибка запуска")+": "+type(error).__name__
            self.changed.emit()
            return False

    def start(self):
        self._monitor.start()

    def stop(self):
        self._closing.set()
        self._monitor.stop()

    def _on_worker_snapshot(self, snapshot):
        if not self._closing.is_set():
            self.snapshot_received.emit(snapshot)

    @Slot(object)
    def _apply_snapshot(self, snapshot):
        if self._closing.is_set():
            return
        server = next((s for s in self._settings["servers"] if s.address == snapshot.address), None)
        if server is None:
            return
        previous_status = self.status
        self.update_snapshot(replace(snapshot, name=snapshot.name or server.label))
        self._status = "udp_count"
        if previous_status != self.status:
            self.changed.emit()


    @Slot(str)
    def _dispatch(self, name):
        if name == "refresh":
            self._status = "UDP: обновление"
            self._monitor.refresh()
        elif name == "connect":
            self.connectServer(self.selected)
            return
        else:
            return
        self.changed.emit()

    @Slot(str, str, result=bool)
    def addServer(self, address, label):
        try:
            address = canonical_address(address)
            if address in self._rows or len(self._rows) >= MAX_SERVERS:
                raise ValueError("duplicate or limit")
            server = Server(address, label.strip()[:80], False)
            self._monitor.replace_servers([*self._settings["servers"], server])
            self.update_snapshot(Snapshot(address=address, name=server.label))
            self._presence.configure(self._settings["friends"],self._rows)
            self.friendsChanged.emit()
            self._status = "Сервер добавлен"
            self._settings_changed()
            self.recordsChanged.emit()
            self.changed.emit()
            return True
        except ValueError:
            self._status = "Неверный адрес, повтор или достигнут лимит"
            self.changed.emit()
            return False

    @Slot(str)
    def toggle(self, key):
        # F8/F9/F10, translation and overlay have not migrated.
        # Never present a simulated active state in live mode.
        return
