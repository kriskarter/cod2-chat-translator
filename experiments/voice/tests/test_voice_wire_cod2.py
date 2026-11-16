"""CoD2 voice wire and untrusted process-memory tests (no real packet capture)."""
from __future__ import annotations

import json
import socket
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_wire_cod2 import (
    OOB_HEADER, VoicePacketJournal, decode_server_voice, parse_ipv4_udp_voice,
)
from voice_cod2_names import (
    CLIENTINFO_SLOTS, CLIENTINFO_STRIDE_13, extract_slot_names, normalize_player_name,
)


def example_voice(slot: int, command: bytes = b"v\x00") -> bytes:
    return OOB_HEADER + command + bytes([2, slot, 3]) + b"abc" + bytes([slot, 2]) + b"12"


def example_udp(udp_payload: bytes, src="203.0.113.11", dst="192.168.1.2") -> bytes:
    ip = bytearray(20)
    ip[0] = 0x45
    ip[8] = 55
    ip[9] = 17
    ip[12:16] = socket.inet_aton(src)
    ip[16:20] = socket.inet_aton(dst)
    struct.pack_into("!H", ip, 2, len(ip) + 8 + len(udp_payload))
    return bytes(ip) + struct.pack("!HHHH", 28960, 3074, len(udp_payload)+8, 0) + udp_payload


class CoD2WireTests(unittest.TestCase):
    def test_real_documented_coD2_13_format(self):
        self.assertEqual(decode_server_voice(example_voice(12)), (12, 12))
        self.assertEqual(
            decode_server_voice(example_voice(63, b"voicePacket\0")), (63, 63)
        )

    def test_udp_envelope_exposes_just_slot_and_endpoint(self):
        obs = parse_ipv4_udp_voice(example_udp(example_voice(12)), now=85.5)
        self.assertEqual(obs.talkers, (12, 12))
        self.assertEqual(obs.source_port, 28960)
        self.assertEqual(obs.destination_port, 3074)
        self.assertEqual(obs.timestamp, 85.5)

    def test_outbound_or_malformed_never_counts_as_speaker(self):
        self.assertEqual(decode_server_voice(b"\x00"*100), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"status\x00data"), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"v\0\x01\x40\x02ab"), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"v\0\x01\x01\x03ab"), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"v\0\x01\x01\x02abc"), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"v\0\x00"), ())
        self.assertEqual(decode_server_voice(OOB_HEADER+b"v\0\xff"), ())

    def test_fragmented_or_truncated_ip_rejected(self):
        voice = example_udp(example_voice(2))
        self.assertIsNone(parse_ipv4_udp_voice(voice[:-1]))
        fragmented = bytearray(voice)
        struct.pack_into("!H", fragmented, 6, 0x2000)
        self.assertIsNone(parse_ipv4_udp_voice(bytes(fragmented)))

    def test_only_one_talker_yields_id_from_multiple_packets(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"events.jsonl"
            journal = VoicePacketJournal(p)
            at = time.monotonic()
            for slot in (12, 12, 12):
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"type":"voice", "at":at,
                        "talkers":[slot], "endpoint_token":"serverX"})+"\n")
            self.assertEqual(journal.match(at-0.1, at+0.1), (12, "single_talker_packets"))

    def test_mixed_talkers_never_assigned_a_name(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"events.jsonl"
            journal = VoicePacketJournal(p)
            at = time.monotonic()
            for slot in (12, 8, 12):
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"type":"voice", "at":at,
                        "talkers":[slot], "endpoint_token":"serverX"})+"\n")
            self.assertEqual(journal.match(at-0.1, at+0.1),
                             (None, "mixed_talkers_or_servers"))

    def test_different_servers_never_confused(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"events.jsonl"
            journal = VoicePacketJournal(p)
            at = time.monotonic()
            for endpoint in ("serverX","serverY"):
                with p.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({"type":"voice", "at":at,
                        "talkers":[12], "endpoint_token":endpoint})+"\n")
            self.assertEqual(journal.match(at-0.1, at+0.1),
                             (None, "mixed_talkers_or_servers"))

    def test_old_events_not_reused_for_new_speech(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/"events.jsonl"
            at = time.monotonic()
            p.write_text(json.dumps({"type":"voice","at":at, "talkers":[12],
                "endpoint_token":"serverX"})+"\n",encoding="utf-8")
            journal = VoicePacketJournal(p)  # skips old contents
            self.assertEqual(journal.match(at-0.1,at+0.1), (None,"no_voice_packets"))


class CoD2NameTableTests(unittest.TestCase):
    def test_slot_offsets_from_coD2x_read_only_layout(self):
        raw = bytearray(CLIENTINFO_SLOTS * CLIENTINFO_STRIDE_13)
        i = 12 * CLIENTINFO_STRIDE_13
        struct.pack_into("<iii", raw, i, 1, 0, 12)
        raw[i+12:i+12+7] = b"^1Pirat"
        ev = extract_slot_names(bytes(raw))
        self.assertEqual(ev.slots, {12: "^1Pirat"})
        self.assertEqual(ev.state, "coD2x_1_3_layout_validated")

    def test_wrong_structure_does_not_guess_names(self):
        raw = bytearray(CLIENTINFO_SLOTS * CLIENTINFO_STRIDE_13)
        for i in range(8):
            struct.pack_into("<iii", raw, i*CLIENTINFO_STRIDE_13, 4, 0, 20)
        ev = extract_slot_names(bytes(raw))
        self.assertEqual(ev.slots, {})
        self.assertEqual(ev.state, "memory_layout_not_validated")

    def test_nick_without_terminator_discarded(self):
        self.assertIsNone(normalize_player_name(b"01234567890123456789012345678901"))


if __name__ == "__main__":
    unittest.main()
