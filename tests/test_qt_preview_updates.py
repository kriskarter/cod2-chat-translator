import hashlib
import io
import json
from pathlib import Path
import pytest

pytest.importorskip("PySide6")
from qt_experiment.preview_updates import (EXE,SUMS,REPO,check_preview_release,download_preview,verify_installer,_allowed_url)

OLD="qt-preview-123456789abc"
NEW="qt-preview-abcdef123456"
PAYLOAD=b"MZ"+b"test payload"*300
DIGEST=hashlib.sha256(PAYLOAD).hexdigest()

def release(tag,date,**extra):
    return dict(tag_name=tag,published_at=date,prerelease=True,body="RC changes",assets=[
        dict(name=EXE,size=len(PAYLOAD),digest="sha256:"+DIGEST,browser_download_url=f"https://github.com/{REPO}/releases/download/{tag}/{EXE}"),
        dict(name=SUMS,browser_download_url=f"https://github.com/{REPO}/releases/download/{tag}/{SUMS}")],**extra)

def candidate():
    return check_preview_release(lambda _: [release(NEW,"2026-11-26T12:00:00Z"),release(OLD,"2026-11-25T12:00:00Z")],installed={"tag":OLD})

def test_no_downgrade_stable_or_foreign_asset():
    old=release(OLD,"2026-11-25T12:00:00Z")
    new=release(NEW,"2026-11-26T12:00:00Z")
    assert candidate()["tag"]==NEW
    assert check_preview_release(lambda _: [old,new],installed={"tag":NEW}) is None
    foreign=release(NEW,"2026-11-26T12:00:00Z")
    foreign["assets"][0]["browser_download_url"]="https://example.com/setup.exe"
    stable=release("v2.0.0","2026-11-27T12:00:00Z");stable["prerelease"]=False
    assert check_preview_release(lambda _: [stable,foreign,old],installed={"tag":OLD}) is None
    assert _allowed_url("https://release-assets.githubusercontent.com/file")
    assert not _allowed_url("https://github.com.example.org/file")
    assert not _allowed_url("http://github.com/file")
    with pytest.raises(ValueError):check_preview_release(lambda _: [new],installed={"tag":OLD})

def test_download_integrity_tampering_cancel(tmp_path):
    c=candidate()
    def opener(url):
        assert url.startswith(f"https://github.com/{REPO}/releases/download/{NEW}/")
        return io.BytesIO((DIGEST+"  "+EXE+"\n").encode() if url.endswith(SUMS) else PAYLOAD)
    package=download_preview(c,tmp_path,opener)
    path=verify_installer(package,tmp_path)
    assert path.read_bytes()==PAYLOAD
    path.write_bytes(b"MZbad")
    with pytest.raises(ValueError):verify_installer(package,tmp_path)
    path.unlink()
    def corrupt(url):
        return opener(url) if url.endswith(SUMS) else io.BytesIO(PAYLOAD[:-1]+b"!")
    with pytest.raises(ValueError):download_preview(c,tmp_path,corrupt)
    assert not list(tmp_path.iterdir())
    with pytest.raises(RuntimeError):download_preview(c,tmp_path,opener,cancelled=lambda:True)
    assert not list(tmp_path.iterdir())
    with pytest.raises(ValueError):download_preview(dict(c,digest="sha256:"+"0"*64),tmp_path,opener)
    assert not list(tmp_path.iterdir())
