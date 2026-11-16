"""Passive CoD2 1.3 voice-packet observer (experimental).

CoD2 1.3 SERVER -> client sends an out-of-band UDP payload:
 FF FF FF FF "v" NUL count [talker-slot byte, size byte, encoded bytes]...
Some Windows-derived servers use "voicePacket" instead of "v".

Sources:
 - janost/vcod docs/research/cod2-protocol.md §1.7 (Mac 1.3 RE)
 - STiXzoOR/cod2-silicon src/PC/server_mp/sv_voice_mp.c

The sniffer NEVER decodes, stores, forwards or modifies voice data.
Only bounded timestamp, source endpoint and talker slot reach the event file.
It is disabled until the user explicitly opts in and grants Windows UAC.
"""
from __future__ import annotations

import ipaddress
import hashlib
import json
import os
import select
import socket
import struct
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

MAX_VOICE_PACKETS = 40
MAX_TALKERS = 64
MAX_EVENT_BYTES = 2 * 1024 * 1024
VOICE_COMMANDS = (b"v\0", b"voicePacket\0")
OOB_HEADER = b"\xff\xff\xff\xff"


@dataclass(frozen=True)
class VoicePacketObservation:
    timestamp: float
    source_ip: str
    source_port: int
    destination_port: int
    talkers: tuple[int, ...]


def decode_server_voice(payload: bytes) -> tuple[int, ...]:
    """Return sender IDs from *strictly validated* CoD2 out-of-band voice."""
    if not payload.startswith(OOB_HEADER):
        return ()
    data = payload[len(OOB_HEADER):]
    command = next((cmd for cmd in VOICE_COMMANDS if data.startswith(cmd)), None)
    if command is None:
        return ()
    at = len(command)
    if at >= len(data):
        return ()
    count = data[at]
    at += 1
    if count == 0 or count > MAX_VOICE_PACKETS:
        return ()
    slots = []
    for _ in range(count):
        if at + 2 > len(data):
            return ()
        slot, length = data[at], data[at + 1]
        at += 2
        if slot >= MAX_TALKERS or length == 0 or at + length > len(data):
            return ()
        slots.append(slot)
        at += length
    # Even an extra byte can indicate a different packet format; fail closed.
    if at != len(data):
        return ()
    return tuple(slots)


def parse_ipv4_udp_voice(packet: bytes, now: float | None = None) -> VoicePacketObservation | None:
    """Read IPv4/UDP headers without trusting malformed lengths/fragments."""
    if len(packet) < 28 or packet[0] >> 4 != 4:
        return None
    ihl = (packet[0] & 0x0F) * 4
    if ihl < 20 or len(packet) < ihl + 8:
        return None
    total_len = struct.unpack_from("!H", packet, 2)[0]
    if total_len < ihl + 8 or total_len > len(packet):
        return None
    if packet[9] != 17:  # UDP
        return None
    frag = struct.unpack_from("!H", packet, 6)[0]
    if frag & 0x3FFF:  # don't handle fragmented voice datagrams
        return None
    src = socket.inet_ntoa(packet[12:16])
    source_port, target_port, udp_len, _ = struct.unpack_from("!HHHH", packet, ihl)
    if source_port == 0 or target_port == 0:
        return None
    if udp_len < 8 or ihl + udp_len != total_len:
        return None
    talkers = decode_server_voice(packet[ihl + 8:ihl + udp_len])
    if not talkers:
        return None
    return VoicePacketObservation(
        timestamp=time.monotonic() if now is None else float(now),
        source_ip=src,
        source_port=source_port,
        destination_port=target_port,
        talkers=talkers,
    )


def local_ipv4_interfaces() -> tuple[str, ...]:
    """Enumerate UP IPv4 interfaces; no WinPcap/Npcap dependency."""
    import psutil

    found = []
    stats = psutil.net_if_stats()
    for adapter, addrs in psutil.net_if_addrs().items():
        if adapter in stats and not stats[adapter].isup:
            continue
        for addr in addrs:
            if addr.family != socket.AF_INET:
                continue
            try:
                ip = ipaddress.ip_address(addr.address)
            except ValueError:
                continue
            if not (ip.is_loopback or ip.is_unspecified or ip.is_link_local):
                found.append(str(ip))
    return tuple(dict.fromkeys(found))[:8]


def parent_still_running(pid: int) -> bool:
    """Limit lifetime of elevated helper to lifetime of its invoking GUI."""
    import psutil

    try:
        parent = psutil.Process(pid)
        return parent.is_running() and parent.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _append_sanitized(out: Path, record: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > MAX_EVENT_BYTES:
        out.replace(out.with_suffix(".previous"))
    # With no packet contents written, the journal is a small metadata-only
    # file that the unelevated app can consume independently.
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def run_windows_packet_helper(parent_pid: int, outfile: Path, stop_file: Path) -> int:
    """Elevated, passive, bounded observer. Never transmits any packet."""
    if os.name != "nt" or parent_pid <= 0:
        return 1
    # Never allow an elevated background process to write to arbitrary files.
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "CoD2VoicePrototype"
    if not os.environ.get("LOCALAPPDATA"):
        return 1
    if (
        outfile.resolve(strict=False).parent != base.resolve(strict=False)
        or stop_file.resolve(strict=False).parent != base.resolve(strict=False)
        or not outfile.name.startswith("voice_packet_probe_")
        or stop_file != outfile.with_suffix(".stop")
    ):
        return 1
    active = []
    try:
        for ip in local_ipv4_interfaces():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                s.bind((ip, 0))
                s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                s.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
                s.setblocking(False)
                active.append(s)
            except OSError:
                try:
                    s.close()
                except (OSError, UnboundLocalError):
                    pass
        if not active:
            _append_sanitized(outfile, {
                "type": "status", "code": "raw_socket_unavailable",
                "reason": "Elevated Windows raw IP capture unavailable",
            })
            return 2
        _append_sanitized(outfile, {
            "type": "status", "code": "listening",
            "interfaces": len(active),
        })
        latest_ping = time.monotonic()
        while parent_still_running(parent_pid) and not stop_file.exists():
            readable, _, _ = select.select(active, [], [], 0.35)
            for s in readable:
                try:
                    frame = s.recv(65535)
                except (BlockingIOError, OSError):
                    continue
                voice = parse_ipv4_udp_voice(frame)
                if voice is None:
                    continue
                # Only metadata is ever written, never actual raw data.
                _append_sanitized(outfile, {
                    "type": "voice",
                    "at": round(voice.timestamp, 6),
                    "slot": None,  # set only if this packet has one sender
                    "talkers": sorted(set(voice.talkers)),
                    "server_port": voice.source_port,
                    "client_port": voice.destination_port,
                    "endpoint_token": hashlib.sha256(
                        (voice.source_ip + ":" + str(voice.source_port)).encode("ascii")
                    ).hexdigest()[:16],
                })
            # A heartbeat distinguishes network silence from a crashed helper.
            now = time.monotonic()
            if now - latest_ping > 5:
                latest_ping = now
                _append_sanitized(outfile, {"type": "status", "code": "listening"})
    except (OSError, ValueError) as exc:
        _append_sanitized(outfile, {
            "type": "status", "code": "capture_failed",
            "reason": type(exc).__name__,
        })
        return 3
    finally:
        for s in active:
            try:
                s.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
                s.close()
            except OSError:
                pass
    return 0


class VoicePacketJournal:
    """Unelevated reader, starts at EOF to avoid stale games and replays."""
    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            self.offset = self.path.stat().st_size
        except OSError:
            self.offset = 0
        self.events: deque[tuple[float, int, str]] = deque(maxlen=320)
        self.status = "ожидаю запуска"
        self._partial = b""

    def poll(self) -> None:
        try:
            size = self.path.stat().st_size
            if self.offset > size:
                # A rotated log begins with fresh events.
                self.offset = 0
                self._partial = b""
            count = min(size - self.offset, 128 * 1024)
            if count <= 0:
                return
            with self.path.open("rb") as f:
                f.seek(self.offset)
                payload = f.read(count)
            self.offset += len(payload)
        except OSError:
            return
        chunks = (self._partial + payload).split(b"\n")
        self._partial = chunks.pop()[:2048]
        for line in chunks[-200:]:
            try:
                message = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(message, dict):
                continue
            if message.get("type") == "status":
                self.status = str(message.get("code", "unknown"))[:100]
            elif message.get("type") == "voice":
                try:
                    at = float(message["at"])
                    slots = message["talkers"]
                    endpoint = str(message.get("endpoint_token", ""))
                    if not 0 < len(slots) <= MAX_VOICE_PACKETS:
                        continue
                    for slot in set(slots):
                        if type(slot) is int and 0 <= slot < MAX_TALKERS:
                            self.events.append((at, slot, endpoint))
                except (ValueError, KeyError, TypeError):
                    continue
        cutoff = time.monotonic() - 10
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def match(self, start: float, finish: float) -> tuple[int | None, str]:
        """Trust a slot only with >=2 voice packets and one unique talker."""
        self.poll()
        if finish < start:
            return None, "invalid_time"
        candidates = [
            (slot, endpoint) for timestamp, slot, endpoint in self.events
            if start - 0.45 <= timestamp <= finish + 0.15
        ]
        if len(candidates) < 2:
            return None, "no_voice_packets"
        slots = {slot for slot, _ in candidates}
        endpoints = {endpoint for _, endpoint in candidates}
        if len(slots) != 1 or len(endpoints) != 1:
            return None, "mixed_talkers_or_servers"
        return next(iter(slots)), "single_talker_packets"
