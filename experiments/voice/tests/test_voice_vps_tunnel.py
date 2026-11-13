"""Offline tests of the automatic CoD2 VPS SSH tunnel."""
from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from voice_vps_tunnel import (
    VoiceSSHTunnel, TunnelError, extract_voice_token,
    validate_ssh_target, read_ssh_target_settings, save_ssh_target_settings,
)


class FakeSSH:
    def __init__(self, transport):
        self.transport = transport
        self.closed = False

    def get_transport(self):
        return self.transport

    def close(self):
        self.closed = True


class EchoChannel:
    """Socket-backed stand-in for the Paramiko Channel API on Windows/Linux."""
    def __init__(self, sock):
        self.sock = sock

    def settimeout(self, timeout):
        self.sock.settimeout(timeout)

    def sendall(self, data):
        self.sock.sendall(data)

    def recv(self, count):
        return self.sock.recv(count)

    def shutdown_write(self):
        self.sock.shutdown(socket.SHUT_WR)

    def close(self):
        self.sock.close()


class MockTransport:
    def __init__(self):
        self.opened = []
        self.active = True

    def is_active(self):
        return self.active

    def open_channel(self, kind, dest, source, timeout):
        assert kind == "direct-tcpip"
        assert dest == ("127.0.0.1", 8765)
        self.opened.append((dest, source))
        channel, peer = socket.socketpair()

        def echo():
            try:
                while True:
                    data = peer.recv(65536)
                    if not data:
                        break
                    peer.sendall(data)
            except OSError:
                pass
            finally:
                peer.close()

        threading.Thread(target=echo, daemon=True).start()
        return EchoChannel(channel)


class TunnelTests(unittest.TestCase):
    def test_target_syntax(self):
        self.assertEqual(
            validate_ssh_target("root@83.171.248.56"),
            ("root", "83.171.248.56"),
        )
        for invalid in ("", "root", "root@", "@host", "root@host;touch x",
                        "root@host:22", "root@host/path", "root@host..",
                        "root@-bad"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_ssh_target(invalid)

    def test_token_extracted_without_logging_secret(self):
        self.assertEqual(
            extract_voice_token("COD2_VOICE_TOKEN=" + "A" * 48 + "\n"),
            "A" * 48,
        )
        for invalid in ("", "COD2_VOICE_TOKEN=short", "PASSWORD=value",
                        "COD2_VOICE_TOKEN=invalid spaces"):
            with self.subTest(invalid=invalid), self.assertRaises(TunnelError):
                extract_voice_token(invalid)

    def test_settings_store_host_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vps_ssh.json"
            self.assertEqual(read_ssh_target_settings(path), "")
            save_ssh_target_settings(path, "root@83.171.248.56")
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"ssh_target": "root@83.171.248.56"},
            )
            self.assertEqual(read_ssh_target_settings(path), "root@83.171.248.56")
            path.write_text('{"ssh_target": "root@host;rm -rf /", "token": "secret"}')
            self.assertEqual(read_ssh_target_settings(path), "")

    def test_tunnel_only_on_ephemeral_loopback_port(self):
        transport = MockTransport()
        ssh = FakeSSH(transport)
        tunnel = VoiceSSHTunnel(ssh, "A" * 48)
        tunnel._start_forwarder(transport)
        try:
            self.assertTrue(tunnel.is_connected())
            host, port = tunnel.url.removeprefix("http://").split(":")
            self.assertEqual(host, "127.0.0.1")
            self.assertNotEqual(int(port), 8765)
            with socket.create_connection((host, int(port)), timeout=2) as client:
                client.settimeout(2)
                client.sendall(b"voice-binary\x00\x01")
                self.assertEqual(client.recv(32), b"voice-binary\x00\x01")
            self.assertEqual(len(transport.opened), 1)
            self.assertEqual(transport.opened[0][0], ("127.0.0.1", 8765))
        finally:
            tunnel.close()
        self.assertTrue(ssh.closed)
        self.assertFalse(tunnel.is_connected())


if __name__ == "__main__":
    unittest.main()
