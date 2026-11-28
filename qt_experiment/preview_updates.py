"""Preview-only GitHub release discovery, bounded download and integrity checks."""
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from .common import ROOT

REPO="kriskarter/cod2-chat-translator"
TAG=re.compile(r"qt-preview-[0-9a-f]{12}$")
EXE="CoD2ChatTranslator_QtPreview_Setup.exe"
SUMS="SHA256SUMS.txt"
MAX_SIZE=350*1024*1024

def installed_build():
    try:
        data=json.loads((ROOT/"qt_build.json").read_text(encoding="utf-8"))
        if (isinstance(data,dict) and data.get("channel") in ("candidate","stable")
                and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", str(data.get("tag","")))
                and re.fullmatch(r"[a-f0-9]{40}",str(data.get("sha","")))):
            return data
        if isinstance(data,dict) and TAG.fullmatch(str(data.get("tag",""))) and isinstance(data.get("sha"),str) and re.fullmatch(r"[0-9a-f]{40}",data["sha"]) and data["sha"].startswith(data["tag"][11:]):
            return data
    except (OSError,ValueError,TypeError): pass
    return {}

def _asset_url(tag,name):
    return f"https://github.com/{REPO}/releases/download/{tag}/{name}"

def _candidate(release):
    if not isinstance(release,dict) or release.get("draft") or not release.get("prerelease"):return None
    tag=str(release.get("tag_name",""))
    if not TAG.fullmatch(tag):return None
    assets={a.get("name"):a for a in release.get("assets",[]) if isinstance(a,dict)}
    if not {EXE,SUMS}.issubset(assets):return None
    for name in (EXE,SUMS):
        if assets[name].get("browser_download_url",_asset_url(tag,name))!=_asset_url(tag,name):return None
    size=assets[EXE].get("size")
    if size is not None and (not isinstance(size,int) or not 0<size<=MAX_SIZE):return None
    digest=assets[EXE].get("digest") or ""
    if digest and not re.fullmatch(r"sha256:[a-fA-F0-9]{64}",digest):return None
    return dict(tag=tag,url=f"https://github.com/{REPO}/releases/tag/{tag}",notes=str(release.get("body") or "")[:12000],
        published=str(release.get("published_at") or ""),size=size,digest=digest.lower())

def check_preview_release(getter=None, installed=None):
    if getter is None:
        from update_client import _get_json
        getter=_get_json
    if installed is None:installed=installed_build()
    if installed.get("channel") in ("candidate", "stable"):
        from update_client import is_newer, verify_update_manifest_signature
        release = getter(f"https://api.github.com/repos/{REPO}/releases/latest")
        tag = release.get("tag_name", "")
        if (release.get("draft") is not False or release.get("prerelease") is not False
                or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+",tag)
                or not (is_newer(tag, installed["tag"]) or (installed["channel"] == "candidate" and tag == installed["tag"]))):
            return None
        name = "CoD2ChatTranslator_Setup.exe"
        assets = {a["name"]: a for a in release.get("assets", [])}
        for asset in (name, "installer-update.json", SUMS):
            if assets.get(asset, {}).get("browser_download_url") != _asset_url(tag,asset):
                return None
        manifest = getter(_asset_url(tag,"installer-update.json"))
        if (not verify_update_manifest_signature(manifest) or manifest.get("asset") != name
                or manifest.get("version") != tag[1:]
                or not re.fullmatch(r"[a-f0-9]{64}",str(manifest.get("sha256","")))):
            raise ValueError("Invalid signed installer manifest")
        return dict(tag=tag, channel="stable", url=f"https://github.com/{REPO}/releases/tag/{tag}",
                    notes=release.get("body",""),size=assets[name].get("size"),digest="sha256:"+manifest["sha256"])
    releases=getter(f"https://api.github.com/repos/{REPO}/releases?per_page=100")
    if not isinstance(releases,list):raise ValueError("Invalid release response")
    candidates=[c for r in releases if (c:=_candidate(r))]
    if not candidates:return None
    current=installed.get("tag")
    if not current:
        # Source/diagnostic mode can display a release, but cannot install.
        return candidates[0]
    baseline=next((c for c in candidates if c["tag"]==current),None)
    if baseline is None:
        baseline=_candidate(getter(f"https://api.github.com/repos/{REPO}/releases/tags/{current}"))
    if not isinstance(baseline,dict) or not baseline["published"]:raise ValueError("Installed preview release cannot be identified")
    newer=[c for c in candidates if c["published"]>baseline["published"] and c["tag"]!=current]
    return max(newer,key=lambda c:c["published"],default=None)

def _allowed_url(url):
    p=urlparse(url)
    return p.scheme=="https" and not p.username and not p.password and p.port in (None,443) and p.hostname in (
        "github.com","release-assets.githubusercontent.com","objects.githubusercontent.com","github-releases.githubusercontent.com")

class _ReleaseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not _allowed_url(newurl):raise ValueError("Untrusted release redirect")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def _open(url):
    if not _allowed_url(url):raise ValueError("Untrusted release URL")
    return urllib.request.build_opener(_ReleaseRedirect()).open(urllib.request.Request(url,headers={"User-Agent":"CoD2ChatTranslator-QtUpdater"}),timeout=20)

def file_sha256(path):
    with Path(path).open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()

def download_preview(candidate,directory,opener=None,cancelled=None):
    opener=opener or _open
    cancelled=cancelled or (lambda:False)
    tag=candidate["tag"]
    stable = candidate.get("channel") == "stable"
    if stable:
        if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+",tag) or not candidate.get("digest"):
            raise ValueError("Invalid stable installer")
    elif not TAG.fullmatch(tag):
        raise ValueError("Invalid preview tag")
    asset = "CoD2ChatTranslator_Setup.exe" if stable else EXE
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    with opener(_asset_url(tag,SUMS)) as response:
        raw=response.read(8193)
    if len(raw)>8192:raise ValueError("Invalid SHA256 manifest")
    match=re.fullmatch(r"([0-9a-fA-F]{64})[ \t]+\*?"+re.escape(asset),raw.decode("ascii").strip())
    if not match:raise ValueError("Invalid SHA256 manifest")
    expected=match.group(1).lower()
    if candidate.get("digest") and candidate["digest"]!="sha256:"+expected:raise ValueError("SHA256 metadata mismatch")
    fd,name=tempfile.mkstemp(prefix=tag+"-",suffix=".part",dir=directory)
    path=Path(name)
    try:
        digest=hashlib.sha256();total=0
        with os.fdopen(fd,"wb") as output,opener(_asset_url(tag,asset)) as response:
            while True:
                if cancelled():raise RuntimeError("Download cancelled")
                chunk=response.read(256*1024)
                if not chunk:break
                total+=len(chunk)
                if total>MAX_SIZE:raise ValueError("Installer too large")
                digest.update(chunk);output.write(chunk)
            output.flush();os.fsync(output.fileno())
        if cancelled():raise RuntimeError("Download cancelled")
        if total==0 or (candidate.get("size") is not None and total!=candidate["size"]) or digest.hexdigest()!=expected:
            raise ValueError("Installer SHA256/size mismatch")
        final=path.with_suffix(".exe");os.replace(path,final)
        return {"path":str(final),"sha256":expected,"tag":tag}
    finally:
        path.unlink(missing_ok=True)

def verify_installer(package,directory):
    path=Path(package["path"])
    if path.parent.resolve()!=Path(directory).resolve() or path.is_symlink() or path.suffix!=".exe" or not path.name.startswith(package["tag"]+"-"):
        raise ValueError("Unexpected installer path")
    if not path.is_file() or path.stat().st_size>MAX_SIZE:raise ValueError("Unexpected installer size")
    if file_sha256(path)!=package["sha256"]:raise ValueError("Installer SHA256 mismatch")
    return path
