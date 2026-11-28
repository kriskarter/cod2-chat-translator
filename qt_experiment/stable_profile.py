"""Import saved player settings once, retaining original files for rollback."""
from pathlib import Path
import json
import os
import tempfile
import sqlite3
from contextlib import closing
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
    root.mkdir(parents=True, exist_ok=True)
    migrate_experience(root, preview)
    migrate_dictionary(root, preview)
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


def snapshot_database(path, destination):
    """SQLite backup includes committed WAL pages and excludes open transactions."""
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=destination.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(name)) as snapshot:
                source.backup(snapshot)
                if snapshot.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise ValueError("Invalid translation experience database")
        try:
            os.link(name, destination)
        except FileExistsError:
            pass
    finally:
        Path(name).unlink(missing_ok=True)


def migrate_experience(root, preview):
    database = "translation_experience.sqlite3"
    backup = root / "before-1.22"
    target = root / database
    if target.exists():
        snapshot_database(target, backup / "stable-experience.sqlite3")
    if not (preview / database).is_file():
        return
    source = backup / "preview-experience.sqlite3"
    snapshot_database(preview / database, source)
    from translation_memory import initialize_schema
    with closing(sqlite3.connect(target.as_uri(), uri=True, timeout=5)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS profile_imports(name TEXT PRIMARY KEY)")
        if db.execute("SELECT 1 FROM profile_imports WHERE name='preview-1.22'").fetchone():
            return
        initialize_schema(db)
        db.execute("ATTACH DATABASE ? AS previous", (source.as_uri() + "?mode=ro",))
        columns = "direction,source,target,style,original,translated,outcome,provider,elapsed_ms,context,last_seen,count"
        db.execute(f"""INSERT INTO observations({columns}) SELECT {columns} FROM previous.observations WHERE true
                    ON CONFLICT(direction,source,target,style,original,translated,outcome,provider)
                    DO UPDATE SET count=observations.count+excluded.count,
                    elapsed_ms=CASE WHEN excluded.last_seen>last_seen THEN excluded.elapsed_ms ELSE elapsed_ms END,
                    context=CASE WHEN excluded.last_seen>last_seen THEN excluded.context ELSE context END,
                    last_seen=max(observations.last_seen,excluded.last_seen)""")
        db.execute("""INSERT INTO timings(direction,provider,outcome,elapsed_ms,ts)
                   SELECT direction,provider,outcome,elapsed_ms,ts FROM previous.timings""")
        if db.execute("PRAGMA main.integrity_check").fetchone() != ("ok",):
            raise ValueError("Experience migration integrity check failed")
        db.execute("INSERT INTO profile_imports VALUES('preview-1.22')")


def migrate_dictionary(root, preview):
    from knowledge_v2 import KnowledgePack, MAX_BYTES
    name = "knowledge_v2.json"
    source, target = preview / name, root / name
    if not source.is_file() or source.stat().st_size > MAX_BYTES:
        return
    data = source.read_bytes()
    try:
        candidate = KnowledgePack.from_bytes(data)
    except (ValueError, TypeError, RecursionError):
        return
    backup = root / "before-1.22"
    backup.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.stat().st_size > MAX_BYTES:
            return
        previous = target.read_bytes()
        try:
            if KnowledgePack.from_bytes(previous).version >= candidate.version:
                return
        except (ValueError, TypeError, RecursionError):
            pass
        create_once(backup / "stable-knowledge.json", previous)
    with tempfile.NamedTemporaryFile(dir=root, delete=False) as f:
        temp = Path(f.name)
        try:
            f.write(data)
        except BaseException:
            f.close()
            temp.unlink(missing_ok=True)
            raise
    try:
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
