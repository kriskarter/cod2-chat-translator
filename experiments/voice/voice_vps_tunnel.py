"""Private in-app SSH tunnel for CoD2 voice recognition.

Requires the existing trusted Windows ~/.ssh/known_hosts entry. The key never
leaves Windows; its passphrase and the VPS ASR token stay only in RAM.
"""
from __future__ import annotations

import json
import os
import re
import select
import socketserver
import threading
from pathlib import Path

REMOTE_ADDRESS = ("127.0.0.1", 8765)
TOKEN_ENV_PATH = "/etc/cod2-fast-voice-experiment.env"
SSH_IDENTITY = Path.home() / ".ssh" / "id_ed25519"
TARGET_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]{0,31})@([A-Za-z0-9][A-Za-z0-9.-]{0,251})$")
TOKEN_RE = re.compile(r"^COD2_VOICE_TOKEN=([A-Za-z0-9_-]{32,256})$", re.MULTILINE)


class TunnelError(RuntimeError):
    """Safe user-facing failure; no passwords, tokens or voice data."""


class KeyUnlockRequired(TunnelError):
    pass


def validate_ssh_target(target: str) -> tuple[str, str]:
    match = TARGET_RE.fullmatch(str(target).strip())
    if not match:
        raise ValueError("Укажи SSH-сервер в формате user@server-ip.")
    username, hostname = match.groups()
    if ".." in hostname or hostname.endswith("."):
        raise ValueError("Некорректный адрес SSH-сервера.")
    return username, hostname


def extract_voice_token(content: str) -> str:
    match = TOKEN_RE.search(content[:4096])
    if not match:
        raise TunnelError("На VPS не найден токен Fast Voice.")
    return match.group(1)


def read_ssh_target_settings(path: Path) -> str:
    """Only a non-sensitive display preference is retained."""
    try:
        if path.stat().st_size > 4096:
            return ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        target = payload.get("ssh_target", "") if isinstance(payload, dict) else ""
        validate_ssh_target(target)
        return target
    except (OSError, ValueError, TypeError):
        return ""


def save_ssh_target_settings(path: Path, target: str) -> None:
    validate_ssh_target(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as stream:
            json.dump({"ssh_target": target}, stream)
        os.chmod(tmp, 0o600)
        tmp.replace(path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


class _LoopbackServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    block_on_close = False
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        pass  # Never log binary voice data or authorization headers.


class VoiceSSHTunnel:
    """Owns a trusted SSH session, local private forwarder and ASR token."""

    def __init__(self, ssh, token: str):
        self._ssh = ssh
        self.token = token
        self._server = None
        self._thread = None
        self.url = ""

    @classmethod
    def connect(cls, target: str, passphrase: str | None = None, *,
                identity_path: Path | None = None):
        import paramiko

        username, hostname = validate_ssh_target(target)
        key_file = Path(identity_path) if identity_path else SSH_IDENTITY
        if not key_file.is_file():
            raise TunnelError("SSH-ключ id_ed25519 не найден у пользователя Windows.")
        ssh = paramiko.SSHClient()
        try:
            # The Windows OpenSSH client already verified this host once.
            # Reject unknown hosts; never click-through or auto-add a new key.
            known_hosts = key_file.parent / "known_hosts"
            trusted_keys = paramiko.HostKeys()
            try:
                trusted_keys.load(str(known_hosts))
            except (OSError, paramiko.SSHException):
                raise TunnelError("Не найден проверенный known_hosts. Сначала проверь SSH-сервер.") from None
            if trusted_keys.lookup(hostname) is None:
                raise TunnelError("Этот VPS ещё не подтверждён в Windows known_hosts.")
            ssh.load_system_host_keys(str(known_hosts))
            ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
            options = dict(
                hostname=hostname, port=22, username=username,
                timeout=8, banner_timeout=8, auth_timeout=8,
                look_for_keys=False,
            )
            if passphrase is not None:
                try:
                    key = paramiko.Ed25519Key.from_private_key_file(
                        str(key_file), password=passphrase
                    )
                except paramiko.PasswordRequiredException:
                    raise KeyUnlockRequired("Ключ SSH защищён парольной фразой.") from None
                except (paramiko.SSHException, ValueError):
                    raise TunnelError("Неверная парольная фраза SSH-ключа.") from None
                ssh.connect(**options, pkey=key, allow_agent=False)
            else:
                try:
                    ssh.connect(**options, allow_agent=True)
                except paramiko.BadHostKeyException:
                    raise  # Key mismatch must never become a passphrase prompt.
                except (paramiko.AuthenticationException, paramiko.SSHException):
                    # OpenSSH agent without an unlocked key can raise either
                    # AuthenticationException or SSHException (no methods).
                    try:
                        paramiko.Ed25519Key.from_private_key_file(str(key_file))
                    except paramiko.PasswordRequiredException:
                        raise KeyUnlockRequired("Нужно разблокировать SSH-ключ.") from None
                    except paramiko.SSHException:
                        raise TunnelError("Не удалось прочитать SSH-ключ.") from None
                    raise TunnelError("SSH-ключ не принят сервером.") from None

            transport = ssh.get_transport()
            if not transport or not transport.is_active():
                raise TunnelError("Не удалось открыть защищённый канал SSH.")
            transport.set_keepalive(25)
            _, stdout, _ = ssh.exec_command("cat " + TOKEN_ENV_PATH, timeout=6)
            content = stdout.read(4096).decode("ascii", errors="replace")
            if stdout.channel.recv_exit_status() != 0:
                raise TunnelError("Нет доступа к токену Fast Voice на VPS.")
            token = extract_voice_token(content)
            tunnel = cls(ssh, token)
            tunnel._start_forwarder(transport)
            return tunnel
        except (KeyUnlockRequired, TunnelError):
            ssh.close()
            raise
        except paramiko.BadHostKeyException:
            ssh.close()
            raise TunnelError(
                "Ключ сервера изменился! Соединение остановлено для безопасности."
            ) from None
        except paramiko.SSHException:
            ssh.close()
            raise TunnelError(
                "SSH отклонил подключение. Проверь известный ключ сервера."
            ) from None
        except (OSError, EOFError, TimeoutError):
            ssh.close()
            raise TunnelError("Нет связи с VPS по SSH. Проверь интернет и адрес.") from None
        except Exception:
            ssh.close()
            raise TunnelError("Не удалось подключить защищённый голосовой канал.") from None

    def _start_forwarder(self, transport) -> None:
        class ForwardHandler(socketserver.BaseRequestHandler):
            def handle(self):
                try:
                    channel = transport.open_channel(
                        "direct-tcpip", REMOTE_ADDRESS, self.client_address,
                        timeout=8,
                    )
                    if channel is None:
                        return
                    try:
                        while transport.is_active():
                            readable, _, _ = select.select(
                                [self.request, channel], [], [], 0.6
                            )
                            if self.request in readable:
                                data = self.request.recv(65536)
                                if not data:
                                    break
                                channel.sendall(data)
                            if channel in readable:
                                data = channel.recv(65536)
                                if not data:
                                    break
                                self.request.sendall(data)
                    finally:
                        channel.close()
                except Exception:
                    # Transport exceptions should not expose voice payloads.
                    pass

        try:
            self._server = _LoopbackServer(("127.0.0.1", 0), ForwardHandler)
            self.url = "http://127.0.0.1:" + str(self._server.server_address[1])
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                kwargs={"poll_interval": 0.2},
                name="CoD2VoicePrivateSSHTunnel", daemon=True,
            )
            self._thread.start()
        except Exception:
            self.close()
            raise TunnelError("Не удалось создать локальный защищённый канал.") from None

    def is_connected(self) -> bool:
        transport = self._ssh.get_transport()
        return bool(transport and transport.is_active() and self._server)

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        self._ssh.close()
