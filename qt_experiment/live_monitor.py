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

from PySide6.QtCore import Qt, Signal, Slot
from server_monitor import Monitor, Snapshot, Server, MAX_SERVERS, canonical_address, load_settings, normalized_name
from server_catalog import launch_connect_command
from .common import PrototypeState, row_from_snapshot


def read_monitor_settings(path: Path | None) -> dict:
    if path is None:
        return load_settings({})
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration root must be an object")
    return load_settings(raw.get("server_monitor", {}))


class LiveMonitorState(PrototypeState):
    snapshot_received = Signal(object)

    def __init__(self, settings: dict, game_exe: Path | None = None):
        super().__init__(tuple(row_from_snapshot(Snapshot(address=s.address, name=s.label))
                               for s in settings["servers"]))
        self._demo = False
        self._status = "UDP: ожидание ответа"
        self._f8 = self._f9 = self._overlay = self._smart = False
        self._settings = settings
        self._game_exe = game_exe
        self._can_connect = bool(os.name == "nt" and game_exe and game_exe.is_file()
                                 and game_exe.name.casefold() in {"cod2mp_s.exe", "cod2mp.exe", "cod2_mp.exe"})
        self._closing = Event()
        self._monitor = Monitor(settings, self._on_worker_snapshot)
        self.snapshot_received.connect(self._apply_snapshot, Qt.ConnectionType.QueuedConnection)
        self.action.connect(self._dispatch)

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
        self.update_snapshot(replace(snapshot, name=snapshot.name or server.label))
        friends = {normalized_name(name) for name in self._settings["friends"]}
        online = {normalized_name(name) for row in self._rows.values()
                  if row.state == "online" for name, _, _ in row.players}
        self._friend_count = len(friends & online)
        count = sum(row.state == "online" for row in self._rows.values())
        self._status = f"UDP: {count} из {len(self._rows)} онлайн"
        self.changed.emit()

    @Slot(str)
    def _dispatch(self, name):
        if name == "refresh":
            self._status = "UDP: обновление"
            self._monitor.refresh()
        elif name == "connect" and self._can_connect and self.selected in self._rows:
            try:
                launch_connect_command(self._game_exe, self.selected)
                self._status = "Запуск CoD2"
            except OSError as error:
                self._status = f"Ошибка запуска: {type(error).__name__}"
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
            self._status = "Сервер добавлен до закрытия приложения"
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
