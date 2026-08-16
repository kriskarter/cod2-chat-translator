from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import re
APP_TEXT = (ROOT / "app.py").read_text(encoding="utf-8")
_m = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)', APP_TEXT, flags=re.M)
if not _m:
    raise SystemExit("APP_VERSION not found")
VERSION = _m.group(1)
DIST = ROOT / "dist"
RELEASE = ROOT / "release"
RELEASE.mkdir(exist_ok=True)

release_cfg_path = ROOT / "release_config.json"
try:
    release_cfg = json.loads(release_cfg_path.read_text(encoding="utf-8")) if release_cfg_path.exists() else {}
except Exception:
    release_cfg = {}
repo = os.environ.get("GITHUB_REPOSITORY", "").strip() or str(release_cfg.get("repository", "")).strip()
release_cfg.update({
    "repository": repo,
    "channel": str(release_cfg.get("channel", "stable") or "stable"),
    "check_on_start": bool(release_cfg.get("check_on_start", True)),
    "developer": str(release_cfg.get("developer", "kriskarter") or "kriskarter"),
    "developer_url": str(release_cfg.get("developer_url", "https://github.com/kriskarter") or "https://github.com/kriskarter"),
})
release_cfg_path.write_text(json.dumps(release_cfg, ensure_ascii=False, indent=2), encoding="utf-8")

required = [DIST / "CoD2ChatTranslator.exe", DIST / "CoD2ChatTranslatorUpdater.exe", release_cfg_path]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing build files: " + ", ".join(missing))

package = RELEASE / "CoD2ChatTranslator_Update.zip"
with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    zf.write(DIST / "CoD2ChatTranslator.exe", "CoD2ChatTranslator.exe")
    zf.write(DIST / "CoD2ChatTranslatorUpdater.exe", "CoD2ChatTranslatorUpdater.exe")
    zf.write(release_cfg_path, "release_config.json")

h = hashlib.sha256()
with package.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
sha = h.hexdigest()
notes = json.loads((ROOT / "release_notes.json").read_text(encoding="utf-8"))
manifest = {
    "version": VERSION,
    "asset": package.name,
    "sha256": sha,
    "notes_ru": notes.get("notes_ru", ""),
    "notes_en": notes.get("notes_en", ""),
}
(RELEASE / "update.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
(RELEASE / "CoD2ChatTranslator_Update.zip.sha256").write_text(f"{sha}  {package.name}\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False, indent=2))
