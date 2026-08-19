from __future__ import annotations

import ctypes
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class GameServer:
    id: str
    name: str
    subtitle: str
    address: str
    discord_url: str = ""
    logo_asset: str = ""


# Встроенный приоритетный сервер.
# Пользовательские серверы позже будут храниться отдельно в config.json.
FEATURED_SERVER = GameServer(
    id="classic-oborona",
    name="CLASSIC OBORONA",
    subtitle="CoD2 1.3 · 24/7",
    address="146.59.34.100:28960",
    discord_url="https://discord.gg/qxwBpzJ",
    logo_asset="assets/servers/oborona.png",
)

SERVER_ADDRESS = FEATURED_SERVER.address


def _path_key(path: Path | str) -> str:
    return os.path.normcase(str(Path(path).expanduser().resolve(strict=False)))


def unique_roots(roots: Iterable[Path | str]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()

    for raw in roots:
        try:
            path = Path(raw).expanduser().resolve(strict=False)
        except Exception:
            continue

        key = _path_key(path)
        if key in seen:
            continue

        seen.add(key)
        result.append(path)

    return result


def find_multiplayer_executable(
    roots: Iterable[Path | str],
) -> Optional[Path]:
    names = (
        "CoD2MP_s.exe",
        "CoD2MP.exe",
        "cod2mp_s.exe",
        "cod2mp.exe",
        "cod2_mp.exe",
    )

    for root in unique_roots(roots):
        for name in names:
            candidate = root / name
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                pass

    return None


def build_connect_command(
    executable: Path | str,
    address: str = SERVER_ADDRESS,
) -> list[str]:
    return [str(Path(executable)), "+connect", address]


def no_window_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def launch_connect_command(
    executable: Path | str,
    address: str = SERVER_ADDRESS,
) -> None:
    executable = Path(executable).expanduser().resolve(strict=False)

    kwargs = {
        "cwd": str(executable.parent),
        "close_fds": True,
    }

    flags = no_window_creationflags()
    if flags:
        kwargs["creationflags"] = flags

    try:
        subprocess.Popen(
            build_connect_command(executable, address),
            **kwargs,
        )
        return
    except OSError as exc:
        # CoD2MP_s.exe может быть настроен на обязательный запуск
        # от администратора. В таком случае запрашиваем UAC только для игры.
        if os.name != "nt" or getattr(exc, "winerror", None) != 740:
            raise

    parameters = subprocess.list2cmdline(["+connect", address])

    result = int(
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(executable),
            parameters,
            str(executable.parent),
            1,
        )
    )

    if result <= 32:
        raise OSError(f"ShellExecuteW failed with code {result}")
