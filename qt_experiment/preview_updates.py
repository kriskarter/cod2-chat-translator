"""Isolated preview channel: only open official release pages, never auto-execute."""
import json
import re
from .common import ROOT

REPO = "kriskarter/cod2-chat-translator"
TAG = re.compile(r"qt-preview-[0-9a-f]{12}$")

def check_preview_release(getter=None):
    if getter is None:
        from update_client import _get_json
        getter = _get_json
    try:
        installed = json.loads((ROOT / "qt_build.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        installed = {}
    releases = getter(f"https://api.github.com/repos/{REPO}/releases?per_page=30")
    if not isinstance(releases, list):
        raise ValueError("Invalid release response")
    for release in releases:
        if not isinstance(release, dict) or release.get("draft") or not release.get("prerelease"):
            continue
        tag = str(release.get("tag_name", ""))
        if not TAG.fullmatch(tag):
            continue
        if not {"CoD2ChatTranslator_QtPreview_Setup.exe", "SHA256SUMS.txt"}.issubset(
                {asset.get("name") for asset in release.get("assets", []) if isinstance(asset, dict)}):
            continue
        if tag == installed.get("tag"):
            return None
        return {"tag": tag, "url": f"https://github.com/{REPO}/releases/tag/{tag}"}
    return None
