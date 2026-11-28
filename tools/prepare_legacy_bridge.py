"""Build a data-only ZIP readable by the published v1.17.4 updater."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile


def prepare(dist, directory):
    executable = dist / "CoD2ChatTranslatorQt.exe"
    if not executable.is_file() or not (dist / "_internal/qt_build.json").is_file():
        raise ValueError("Missing frozen Qt distribution")
    manifest = json.loads((directory / "installer-update.json").read_text(encoding="utf-8"))
    package = directory / "CoD2ChatTranslator_Update.zip"
    # The legacy updater relaunches the original executable name. Keeping that
    # name also preserves shortcuts in custom installation directories.
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for path in sorted(dist.rglob("*")):
            if path.is_file():
                archive.write(path, "CoD2ChatTranslator.exe" if path == executable else path.relative_to(dist))
        root = Path(__file__).resolve().parents[1]
        for name in ("COPYRIGHT.md", "THIRD_PARTY_NOTICES.txt", "docs/QT_THIRD_PARTY_NOTICES.txt"):
            archive.write(root / name, Path(name).name)
        inventory = root / "qt_dependency_inventory.txt"
        if inventory.is_file():
            archive.write(inventory, inventory.name)
        for path in (root / "docs/qt_licenses").glob("*"):
            if path.is_file():
                archive.write(path, "licenses/" + path.name)
    with package.open("rb") as stream:
        manifest.update(asset=package.name, sha256=hashlib.file_digest(stream, "sha256").hexdigest())
    (directory / "update.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
