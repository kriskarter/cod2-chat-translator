"""Safe local CoD2 voice capture bootstrap; no process injection or remote controls.

Changes only user's existing multiplayer config files, with permanent backups.
If Multiplayer is already running, writes are deferred until it exits: the
game overwrites config_mp.cfg when shutting down.
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

_ALLOWED_DVARS = {"winvoice_save_voice": 1, "logfile": 2}
_CFG_NAME = "config_mp.cfg"
MAX_CONFIGS = 80
MAX_CFG_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class CaptureSetup:
    found: int = 0
    ready: int = 0
    changed: int = 0
    deferred: int = 0
    failed: int = 0
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.found > 0 and self.ready == self.found and not self.failed


def game_root_for_voice(voice_path: Path | str) -> Path:
    """voice.wav is created in the install root, not in a profile folder."""
    path = Path(voice_path).expanduser().resolve(strict=False)
    return path.parent


def _config_paths_under(root: Path) -> list[Path]:
    found: list[Path] = []
    bases = [root]
    try:
        children = [p for p in root.iterdir() if p.is_dir()]
    except (OSError, PermissionError):
        children = []
    bases += children
    for child in children:
        if child.name.lower() == "mods":
            try:
                bases += [p for p in child.iterdir() if p.is_dir()]
            except (OSError, PermissionError):
                pass
    for base in bases[:100]:
        try:
            if (base / _CFG_NAME).is_file():
                found.append((base / _CFG_NAME).resolve())
            players = base / "players"
            if not players.is_dir():
                continue
            # Bounded layout: players/<profile>/config_mp.cfg and one nested
            # level for portable/mod configurations, no recursive disk search.
            for player_dir in players.iterdir():
                if not player_dir.is_dir():
                    continue
                candidate = player_dir / _CFG_NAME
                if candidate.is_file():
                    found.append(candidate.resolve())
                try:
                    for child in player_dir.iterdir():
                        if child.is_dir() and (child / _CFG_NAME).is_file():
                            found.append((child / _CFG_NAME).resolve())
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            continue
    return found


def find_configs(voice_path: Path | str) -> list[Path]:
    root = game_root_for_voice(voice_path)
    locations = [root]
    # Windows VirtualStore mirrors protected Program Files installations.
    appdata = os.getenv("LOCALAPPDATA", "")
    if os.name == "nt" and appdata and root.drive:
        try:
            rel = root.relative_to(Path(root.drive + "\\"))
            mirror = Path(appdata) / "VirtualStore" / rel
            if mirror.is_dir():
                locations.append(mirror)
        except (ValueError, OSError):
            pass
    found: dict[str, Path] = {}
    for location in locations:
        for path in _config_paths_under(location):
            key = os.path.normcase(str(path))
            if key not in found:
                found[key] = path
            if len(found) >= MAX_CONFIGS:
                return list(found.values())
    return list(found.values())


def _dvar_regex(dvar: str) -> re.Pattern[bytes]:
    # Strictly restrict dvar to our small allowlist to avoid arbitrary edits.
    if dvar not in _ALLOWED_DVARS:
        raise ValueError("Unknown CoD2 setting")
    key = re.escape(dvar.encode("ascii"))
    return re.compile(
        rb"(?im)^([ \t]*(?:(?:seta|set|setu)[ \t]+)?" + key +
        rb"[ \t]+)(\"?[-+]?\d+\"?)([ \t]*(?://[^\r\n]*)?)(\r?\n|$)"
    )


def read_dvar(contents: bytes, dvar: str) -> int | None:
    values = _dvar_regex(dvar).findall(contents)
    if not values:
        return None
    try:
        return int(values[-1][1].replace(b'"', b""))
    except ValueError:
        return None


def patch_config(contents: bytes, settings: dict[str, int]) -> bytes:
    """Preserve every unrelated byte of arbitrary-encoding CoD2 configs."""
    output = contents
    newline = b"\r\n" if b"\r\n" in output else b"\n"
    for name, target in settings.items():
        if name not in _ALLOWED_DVARS or target != _ALLOWED_DVARS[name]:
            raise ValueError("Only known local capture settings are permitted")
        regex = _dvar_regex(name)
        target_bytes = str(target).encode("ascii")
        if regex.search(output):
            output = regex.sub(
                lambda match: match.group(1) + b'"' + target_bytes + b'"' +
                match.group(3) + match.group(4),
                output,
            )
        else:
            if output and not output.endswith((b"\r", b"\n")):
                output += newline
            output += b'seta ' + name.encode("ascii") + b' "' + target_bytes + b'"' + newline
    return output


def write_config_with_backup(cfg_path: Path, settings: dict[str, int]) -> bool:
    """Never overwrite .cod2voice.bak; atomic replace with original permissions."""
    cfg = Path(cfg_path)
    data = cfg.read_bytes()
    if len(data) > MAX_CFG_BYTES:
        raise ValueError("config_mp.cfg unexpectedly large")
    updated = patch_config(data, settings)
    if data == updated:
        return False
    backup = cfg.with_name(cfg.name + ".cod2voice.bak")
    temp = cfg.with_name(cfg.name + ".cod2voice.tmp")
    if not backup.exists():
        shutil.copy2(cfg, backup)
    try:
        temp.write_bytes(updated)
        shutil.copymode(cfg, temp)
        os.replace(temp, cfg)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
    return True


def ensure_voice_capture(
    voice_path: Path | str,
    *,
    game_running: bool,
    include_logfile: bool = False,
) -> CaptureSetup:
    """Configure known multiplayer profiles; defer any change while game runs."""
    try:
        if Path(voice_path).name.casefold() != "voice.wav":
            return CaptureSetup(error="Нужен исходный voice.wav из папки CoD2")
        paths = find_configs(voice_path)
        settings = {"winvoice_save_voice": 1}
        if include_logfile:
            settings["logfile"] = 2
        ready = changed = deferred = failed = 0
        last_error = ""
        for cfg in paths:
            try:
                data = cfg.read_bytes()
                if all(read_dvar(data, k) == v for k, v in settings.items()):
                    ready += 1
                    continue
                if game_running:
                    deferred += 1
                    continue
                if write_config_with_backup(cfg, settings):
                    changed += 1
                verified = cfg.read_bytes()
                if all(read_dvar(verified, k) == v for k, v in settings.items()):
                    ready += 1
                else:
                    failed += 1
                    last_error = "Не удалось подтвердить настройки в " + str(cfg)
            except (OSError, ValueError) as exc:
                failed += 1
                last_error = f"{cfg.name}: {exc}"
        return CaptureSetup(
            found=len(paths), ready=ready, changed=changed,
            deferred=deferred, failed=failed, error=last_error,
        )
    except (OSError, ValueError) as exc:
        return CaptureSetup(error=str(exc))
