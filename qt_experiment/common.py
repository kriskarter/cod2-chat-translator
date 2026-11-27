"""Shared, explicitly experimental state for the two Qt rendering candidates.

The production translator still starts through app.py. No user configuration is
read or written by these prototypes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from html import escape

from .font_setup import prepare_font_environment, ensure_ui_font
prepare_font_environment()

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuickControls2 import QQuickStyle

# The native Windows style does not support our custom control backgrounds.
# Use the portable Qt base style before loading any QML Controls.
QQuickStyle.setStyle("Basic")

from server_monitor import Snapshot, color_runs, plain_name, player_ping_quality
from .friend_presence import display_name, rich_name

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "ui_wwii"


@dataclass(frozen=True)
class MonitorRow:
    address: str
    name: str
    map_name: str
    population: str
    ping: str
    state: str
    players: tuple[tuple[str, int | None, int | None], ...] = ()


def row_from_snapshot(snapshot: Snapshot) -> MonitorRow:
    """Keep stale/limited states visible without inventing player data."""
    return MonitorRow(
        snapshot.address, snapshot.name or snapshot.address,
        snapshot.map_name or "—",
        f"{snapshot.clients}/{snapshot.max_clients}" if snapshot.clients is not None and snapshot.max_clients is not None else "—",
        f"{snapshot.ping_ms} ms" if snapshot.ping_ms is not None and snapshot.ping_ms > 0 else "—",
        snapshot.state,
        tuple((p.raw_name, p.score, p.ping) for p in snapshot.players),
    )


class PrototypeState(QObject):
    changed = Signal()
    rowsChanged = Signal()
    friendsChanged = Signal()
    friendNotice = Signal(str,str)
    action = Signal(str)

    def __init__(self, rows: tuple[MonitorRow, ...] = ()):
        super().__init__()
        ensure_ui_font(QGuiApplication.instance())
        self._f8 = True
        self._f9 = True
        self._overlay = True
        self._smart = True
        self._demo = True
        self._status = "Демонстрационные данные"
        self._friend_count = 0
        self._can_connect = True
        self._selected = rows[0].address if rows else ""
        self._rows = {row.address: row for row in rows}

    @Property(str, notify=changed)
    def uiLanguage(self): return "ru"

    @Slot(str, result=str)
    def trText(self, text):
        from .ui_text import translate
        return translate(text,self.uiLanguage)

    @Property(bool, constant=True)
    def serverManagementAvailable(self): return False

    @Property(bool, constant=True)
    def settingsWritable(self): return False

    @Property(bool, constant=True)
    def overlayAvailable(self): return False

    @Property(bool, constant=True)
    def translationAvailable(self): return False

    @Property(bool, notify=changed)
    def gamePrivilegeMismatch(self): return False

    @Property(bool, constant=True)
    def demo(self): return self._demo

    @Property(str, notify=changed)
    def status(self):
        if self._status == "udp_count":
            online = sum(row.state == "online" for row in self._rows.values())
            return f"UDP · {online}/{len(self._rows)} " + self.trText("online")
        return self.trText(self._status)

    @Property(int, notify=changed)
    def friendCount(self): return self._friend_count

    @Property("QVariantList", notify=friendsChanged)
    def friendRows(self): return []

    @Property(str, notify=friendsChanged)
    def friendSaveError(self): return ""

    @Slot(str, result=str)
    def friendDisplayName(self, raw): return display_name(raw)

    @Slot(str, result=bool)
    def isFriend(self, raw): return self._is_friend(raw)

    @Slot(str, result=bool)
    def toggleFriend(self, raw): return False

    @Slot(str, result=bool)
    def connectServer(self, address): return False

    @Slot(str)
    def copyText(self, value):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(value)

    @Property(bool, notify=changed)
    def canConnect(self): return self._can_connect

    @Slot(str, str, result=str)
    def serverAddressPreview(self, host, port):
        from server_monitor import address_from_fields
        try:
            return address_from_fields(host, port)
        except ValueError:
            return ""

    @Slot(str, result="QVariantMap")
    def serverAddressFields(self, address):
        from server_monitor import address_fields
        try:
            host, port = address_fields(address)
            return {"host": host, "port": port}
        except ValueError:
            return {}

    @Slot(str, str, result="QVariantMap")
    def pastedServerFields(self, host, port):
        if not (host.count(":") == 1 or host.startswith("[") and "]:" in host):
            return {}
        return self.serverAddressFields(host)

    @Slot(str, str, result=bool)
    def addServer(self, address, label):
        return False

    @Property(bool, notify=changed)
    def f8(self): return self._f8

    @Property(bool, notify=changed)
    def f9(self): return self._f9

    @Property(bool, notify=changed)
    def overlay(self): return self._overlay

    @Property(bool, notify=changed)
    def smart(self): return self._smart

    @Property(str, notify=changed)
    def selectedPopulation(self):
        row = self._rows.get(self._selected)
        return row.population if row else "—"

    @Property(str, notify=changed)
    def selected(self): return self._selected

    def _is_favorite(self, address):
        return False

    @Property('QVariantList', notify=rowsChanged)
    def rows(self):
        return [dict(address=r.address, name=r.name, map=r.map_name,
                     population=r.population, ping=r.ping.replace(" ms", " " + self.trText("мс")), state=r.state, favorite=self._is_favorite(r.address))
                for r in self._rows.values()]

    def _is_friend(self, name): return False

    @Property('QVariantList', notify=changed)
    def players(self):
        row = self._rows.get(self._selected)
        return [dict(name=display_name(name), rawName=name, address=self._selected,
                     richName=rich_name(name),
                     score=score if score is not None else '—',
                     ping=ping if ping is not None and ping > 0 else '—', pingQuality=player_ping_quality(ping), favorite=self._is_friend(name))
                for name, score, ping in (row.players if row else ())]

    def update_snapshot(self, snapshot: Snapshot):
        row = row_from_snapshot(snapshot)
        if self._rows.get(row.address) != row:
            self._rows[row.address] = row
            self.rowsChanged.emit()
            if not self._selected:
                self._selected = row.address
            self.changed.emit()

    @Slot(str)
    def select(self, address):
        if address in self._rows and address != self._selected:
            self._selected = address
            self.changed.emit()

    @Slot(str)
    def toggle(self, key):
        attr = '_' + key
        if key in {'f8', 'f9', 'overlay', 'smart'}:
            setattr(self, attr, not getattr(self, attr))
            self.changed.emit()
            self.action.emit(key)

    @Slot(str)
    def request(self, key):
        self.action.emit(key)


def preview_state() -> PrototypeState:
    """Static comparison dataset, never used by the production entry point."""
    return PrototypeState((
        MonitorRow('preview:1', 'Classic OBORONA', 'Toujane', '24/32', '42 ms', 'online',
                   (('^1Sniper', 36, 40), ('^4KriS', 28, 44), ('^2Medic', 21, 56), ('^6Ghost', 17, 61))),
        MonitorRow('preview:2', 'Hardcore Frontline', 'Carentan', '12/24', '58 ms', 'online'),
        MonitorRow('preview:3', 'Old School Rifles', 'Burgundy', '0/20', '—', 'offline'),
    ))
