"""Import saved player settings once, retaining original files for rollback."""
from pathlib import Path
import json
import os
import tempfile
from app import deep_merge


def create_once(path, payload):
    """Publish a complete file without replacing an existing or competing copy."""
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(name, path)
        except FileExistsError:
            pass
    finally:
        Path(name).unlink(missing_ok=True)


def migrate(stable_config, preview):
    root = stable_config.parent
    target = root / "qt_settings.json"
    if target.exists():
        return target
    backups = root / "before-1.22"
    result = {}
    def load(path, label):
        if not path.exists():
            return {}
        data = path.read_bytes()
        backups.mkdir(exist_ok=True)
        create_once(backups / label, data)
        values = json.loads(data.decode("utf-8-sig"))
        if not isinstance(values, dict):
            raise ValueError(f"Invalid settings: {path.name}")
        return values

    result.update(load(stable_config, "stable-config.json"))
    old_chat = load(root / "outgoing_chat.json", "outgoing-chat.json")
    for source, key in (("source_language","outgoing_source_language"),
                        ("target_language","outgoing_target_language"), ("enabled","outgoing_enabled")):
        if source in old_chat:
            result.setdefault(key, old_chat[source])
    qt = load(preview / "qt_settings.json", "preview-settings.json")
    legacy_monitor = result.get("server_monitor", {})
    legacy_profiles = result.get("server_profiles")
    result = deep_merge(result, qt)
    # Both installations can contain independent favourites and friends.
    def combine(primary, older, field):
        def key(item):
            value = item.get(field, "") if isinstance(item, dict) else item
            return str(value).casefold()
        merged = list(primary)
        seen = {key(item) for item in primary}
        for item in older:
            if key(item) not in seen:
                merged.append(item)
                seen.add(key(item))
        return merged

    if isinstance(legacy_monitor, dict) and isinstance(qt.get("server_monitor"), dict):
        for name, field in (("servers", "address"), ("friends", "name")):
            newer = qt["server_monitor"].get(name)
            older = legacy_monitor.get(name)
            if isinstance(newer, list) and isinstance(older, list):
                result["server_monitor"][name] = combine(newer, older, field)
    if isinstance(qt.get("server_profiles"), list):
        if isinstance(legacy_profiles, list):
            result["server_profiles"] = combine(qt["server_profiles"], legacy_profiles, "path")
    if result:
        create_once(target, json.dumps(result, ensure_ascii=False, indent=2).encode())
    return target
