"""Prepare release text and the installer manifest before signing a stable release."""
import hashlib
import json
from pathlib import Path
import sys

def prepare(directory, version):
    exe = directory / "CoD2ChatTranslator_Setup.exe"
    with exe.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if (directory / "SHA256SUMS.txt").read_text().strip().split() != [digest, exe.name]:
        raise ValueError("Installer checksum mismatch")
    values = dict(asset=exe.name, version=version, sha256=digest)
    notes = Path(__file__).resolve().parents[1] / "docs" / "release-1.22"
    for language in ("en","ru","uk"):
        values["notes_"+language] = (notes / (language+".md")).read_text(encoding="utf-8").replace("SHA-256: SHA256SUMS.txt", "SHA-256: "+digest)
    (directory / "installer-update.json").write_text(json.dumps(values,ensure_ascii=False,indent=2),encoding="utf-8")
    (directory / "RELEASE_NOTES.md").write_text("\n\n---\n\n".join(values["notes_"+lang] for lang in ("en","ru","uk")),encoding="utf-8")

if __name__ == "__main__":
    prepare(Path(sys.argv[1]),sys.argv[2])
