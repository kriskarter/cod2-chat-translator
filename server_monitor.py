"""Read-only Call of Duty 2 server monitor (Quake 3 UDP query protocol).

This module has no Tk dependencies. Network requests run in a dedicated daemon
worker and hand immutable results to the caller's UI queue.
"""
from __future__ import annotations

import re
import ipaddress
import socket
import threading
import time
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable

from server_catalog import FEATURED_SERVER


MAX_SERVERS = 32
DEFAULT_PORT = 28960
_COLOR = re.compile(r"\^[0-9]")
_PLAYER = re.compile(r'^\s*(-?\d+)\s+(-?\d+)\s+"(.*)"\s*$')
_HOST = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_MOJIBAKE = re.compile(r"[À-ÿ]{3,}")


def _legacy_name(value: str) -> str:
    # CoD2 has no encoding marker. Cyrillic community servers often send
    # Windows-1251 names; retain Western names with only isolated accents.
    if _MOJIBAKE.search(value):
        return value.encode("cp1252", errors="replace").decode("cp1251", errors="replace")
    return value


def plain_name(value: str) -> str:
    """Interpret ^^ as a literal caret, and ^<char> as CoD color markup."""
    marker = "\ue000"
    return unicodedata.normalize("NFKC", _COLOR.sub("", value.replace("^^", marker))
                                 .replace(marker, "^")).strip()


def normalized_name(value: str) -> str:
    return plain_name(value).casefold()


def color_runs(value: str) -> tuple[tuple[str, str], ...]:
    """Keep the game's original text and color changes for UI rendering."""
    palette = {"0": "#242424", "1": "#E56A61", "2": "#87D970",
               "3": "#E6C66E", "4": "#789FEC", "5": "#7BCFD6",
               "6": "#CB87DC", "7": "#F0E8D3", "8": "#E8A56C",
               "9": "#A8A8A8"}
    runs: list[tuple[str, str]] = []
    buf = ""
    color = palette["7"]
    i = 0
    while i < len(value):
        if value[i:i+2] == "^^":
            buf += "^"; i += 2
        elif value[i:i+1] == "^" and i + 1 < len(value) and value[i+1] in palette:
            if buf:
                runs.append((buf, color)); buf = ""
            color = palette.get(value[i+1], color)
            i += 2
        else:
            buf += value[i]; i += 1
    if buf:
        runs.append((buf, color))
    return tuple(runs)


def player_ping_quality(value: int | None) -> str:
    """Classify only valid reported latency; a reported zero is ambiguous."""
    if value is None:
        return "missing"
    if value < 0:
        return "missing"
    if value == 0:
        return "server_zero"
    if value < 70:
        return "good"
    if value < 160:
        return "fair"
    return "poor"


def parse_address(value: str) -> tuple[str, int]:
    if any(ch in value for ch in "\n\r\t"):
        raise ValueError("Invalid server address")
    raw = value.strip()
    if not raw or any(ch in raw for ch in "/\\\n\r\t @"):
        raise ValueError("Invalid server address")
    if raw.startswith("["):
        end = raw.find("]")
        if end < 0 or raw[end+1:end+2] not in ("", ":"):
            raise ValueError("Invalid IPv6 address")
        host = raw[1:end]
        try:
            socket.inet_pton(socket.AF_INET6, host)
        except OSError as exc:
            raise ValueError("Invalid IPv6 address") from exc
        host = str(ipaddress.IPv6Address(host))
        suffix = raw[end+2:]
    else:
        if raw.count(":") > 1:
            raise ValueError("Wrap IPv6 address in brackets")
        host, sep, suffix = raw.partition(":")
        if not _HOST.fullmatch(host) or ".." in host or host.isdigit():
            raise ValueError("Invalid host")
        if all(c in "0123456789." for c in host):
            try:
                host = str(ipaddress.IPv4Address(host))
            except ValueError as exc:
                raise ValueError("Invalid IPv4 address") from exc
        elif any(not part or len(part) > 63 or part.startswith("-") or part.endswith("-") for part in host.split(".")):
            raise ValueError("Invalid host")
    if suffix and not suffix.isascii():
        raise ValueError("Invalid port")
    if suffix and not suffix.isdigit():
        raise ValueError("Invalid port")
    if raw.endswith(":") or not 1 <= int(suffix or DEFAULT_PORT) <= 65535:
        raise ValueError("Invalid port")
    return host, int(suffix or DEFAULT_PORT)


def canonical_address(value: str) -> str:
    host, port = parse_address(value)
    return f"[{host.lower()}]:{port}" if ":" in host else f"{host.lower()}:{port}"


def address_fields(value: str) -> tuple[str, str]:
    host, port = parse_address(value)
    return host, str(port)


def address_from_fields(host: str, port: str) -> str:
    """An explicitly pasted host:port takes precedence over the port field."""
    host = host.strip()
    if host.startswith("[") and "]:" in host or host.count(":") == 1:
        return canonical_address(host)
    if not port.strip() or not port.strip().isascii() or not port.strip().isdigit():
        raise ValueError("Invalid port")
    if ":" in host and not host.startswith("["):
        host = "[" + str(ipaddress.IPv6Address(host)) + "]"
    return canonical_address(host + ":" + port.strip())


@dataclass(frozen=True)
class Server:
    address: str
    label: str = ""
    favorite: bool = False


@dataclass(frozen=True)
class Player:
    raw_name: str
    score: int | None
    ping: int | None

    @property
    def name(self) -> str:
        return plain_name(self.raw_name)


@dataclass(frozen=True)
class Snapshot:
    address: str
    state: str = "waiting"  # waiting, online, limited, offline
    name: str = ""
    map_name: str = ""
    game_type: str = ""
    clients: int | None = None
    max_clients: int | None = None
    ping_ms: int | None = None
    players: tuple[Player, ...] = ()
    last_success: datetime | None = None
    error: str = ""


def _rules(raw: str) -> dict[str, str]:
    parts = raw.strip().lstrip("\\").split("\\")
    return {parts[i].lower(): parts[i+1] for i in range(0, len(parts)-1, 2)}


def parse_response(address: str, payload: bytes, elapsed_ms: int) -> Snapshot:
    if len(payload) > 65507 or not payload.startswith(b"\xff\xff\xff\xff"):
        raise ValueError("Not a game server response")
    decoded = payload[4:].decode("cp1252", errors="replace")
    header, sep, rest = decoded.partition("\n")
    if not sep or header not in ("statusResponse", "infoResponse"):
        raise ValueError("Unsupported game server response")
    rules_line, _, player_lines = rest.partition("\n")
    info = _rules(rules_line)
    game = info.get("gamename", "")
    if game and "call of duty 2" not in game.casefold() and game.casefold() != "cod2":
        raise ValueError("Server is not Call of Duty 2")
    players: list[Player] = []
    if header == "statusResponse":
        for line in player_lines.splitlines()[:128]:
            match = _PLAYER.fullmatch(line.rstrip("\r"))
            if match:
                players.append(Player(_legacy_name(match[3]), int(match[1]), int(match[2])))
    def number(key):
        try:
            return max(0, int(info[key]))
        except (KeyError, ValueError):
            return None
    return Snapshot(
        address=address, state="online" if header == "statusResponse" else "limited",
        name=plain_name(_legacy_name(info.get("sv_hostname", ""))),
        map_name=info.get("mapname", ""),
        game_type=info.get("g_gametype", info.get("gametype", "")),
        clients=len(players) if header == "statusResponse" else number("clients"),
        max_clients=number("sv_maxclients"), ping_ms=elapsed_ms,
        players=tuple(players), last_success=datetime.now(timezone.utc),
    )


def query_server(address: str, *, timeout: float = 1.5) -> Snapshot:
    host, port = parse_address(address)
    error = "No response"
    try:
        peers = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)[:4]
    except OSError as exc:
        return Snapshot(address=address,state="offline",error=type(exc).__name__)
    for command in (b"getstatus", b"getinfo"):
        for family, socktype, proto, _, peer in peers:
            try:
                with socket.socket(family, socktype, proto) as sock:
                    sock.settimeout(timeout)
                    sock.connect(peer)
                    start = time.monotonic()
                    sock.send(b"\xff\xff\xff\xff" + command)
                    payload = sock.recv(65507)
                    result = parse_response(address, payload, round((time.monotonic()-start)*1000))
                    # A getstatus request may yield infoResponse on certain mods.
                    return result
            except (OSError, ValueError) as exc:
                error = type(exc).__name__ if isinstance(exc, OSError) else str(exc)
    return Snapshot(address=address, state="offline", error=error)


def load_settings(raw: object) -> dict:
    """Normalize untrusted config without discarding a valid existing server."""
    source = raw if isinstance(raw, dict) else {}
    servers = []
    seen = set()
    entries = source.get("servers", [])
    for item in entries if isinstance(entries, list) else []:
        if not isinstance(item, dict):
            continue
        try:
            address = canonical_address(str(item.get("address", "")))
        except ValueError:
            continue
        if address in seen or len(servers) >= MAX_SERVERS:
            continue
        seen.add(address)
        servers.append(Server(address, str(item.get("label", ""))[:80], bool(item.get("favorite", False))))
    if not seen and "servers" not in source:
        servers.append(Server(FEATURED_SERVER.address, FEATURED_SERVER.name, True))
    friends = []
    for value in source.get("friends", []) if isinstance(source.get("friends", []), list) else []:
        label = plain_name(str(value))[:48]
        if label and normalized_name(label) not in {normalized_name(f) for f in friends}:
            friends.append(label)
    try:
        interval = max(30, min(600, int(source.get("refresh_seconds", 60))))
    except (ValueError, TypeError):
        interval = 60
    return {"servers": servers, "friends": friends[:100],
            "refresh_seconds": interval, "notify_friends": bool(source.get("notify_friends", False))}


def dump_settings(settings: dict) -> dict:
    return {"servers": [vars(server).copy() for server in settings["servers"]],
            "friends": list(settings["friends"]),
            "refresh_seconds": settings["refresh_seconds"],
            "notify_friends": settings["notify_friends"]}


class Monitor:
    """One daemon worker; query never blocks Tk or translation workers."""
    def __init__(self, settings: dict, callback: Callable[[Snapshot], None], *, round_callback=None):
        self.settings = settings
        self.callback = callback
        self.round_callback = round_callback
        self.snapshots: dict[str, Snapshot] = {}
        self._lock = threading.Lock()
        self._revision = 0
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="CoD2ServerMonitor", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set(); self._wake.set()

    def refresh(self):
        self._wake.set()

    def replace_servers(self, servers):
        """Replace the worker input under the same lock used for snapshots."""
        with self._lock:
            previous = {s.address for s in self.settings["servers"]}
            current = {s.address for s in servers}
            self.settings["servers"] = list(servers)
            if current != previous:
                self._revision += 1
                self.snapshots = {a:s for a,s in self.snapshots.items() if a in current}
        self.refresh()

    def _run(self):
        while not self._stop.is_set():
            with self._lock:
                servers = tuple(self.settings["servers"])
                interval = self.settings["refresh_seconds"]
                revision = self._revision
            round_snapshots = []
            for server in servers:
                if self._stop.is_set():
                    break
                snapshot = query_server(server.address)
                with self._lock:
                    if revision != self._revision:
                        break
                    old = self.snapshots.get(server.address)
                    if snapshot.state == "offline" and old:
                        snapshot = replace(snapshot, last_success=old.last_success)
                    self.snapshots[server.address] = snapshot
                self.callback(snapshot)
                round_snapshots.append(snapshot)
            with self._lock:
                current_round = revision == self._revision
            if current_round and self.round_callback is not None and not self._stop.is_set():
                self.round_callback(tuple(round_snapshots))
            self._wake.wait(interval)
            self._wake.clear()
