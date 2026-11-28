import json
import pytest
from smart_engine import DEFAULT_ENGINE, TranslationRequest
from outgoing_chat import translate_outgoing_text
from qt_experiment.stable_profile import migrate
from qt_experiment.preview_updates import check_preview_release


@pytest.mark.parametrize("token", ["discord.gg/qxwBpzJ", "https://github.com/kriskarter/cod2-chat-translator",
    "148.251.139.73:12345", "example.com", "https://example.com/chat?mode=gg", "player@example.com",
    "[2001:db8::1]:28960", "2001:db8::1"])
def test_protected_token_never_reaches_provider(token):
    def provider(*args):
        pytest.fail(f"Technical fragment reached provider: {args}")
    message = "gg! " + token
    result = DEFAULT_ENGINE.translate(TranslationRequest(message, "ru"), provider)
    assert result.safe and result.text == "хорошая игра! " + token
    for smart in (True, False):
        assert translate_outgoing_text(token, "ru", smart_enabled=smart, transport=provider) == token


def test_discord_invitation_prose_is_translated():
    calls = []
    def provider(text, *languages):
        calls.append(text)
        return "Присоединяйтесь к нашему Discord:"
    result = DEFAULT_ENGINE.translate(TranslationRequest("Join our Discord: discord.gg/qxwBpzJ", "ru"), provider)
    assert calls == ["Join our Discord:"]
    assert result.text == "Присоединяйтесь к нашему Discord: discord.gg/qxwBpzJ"


def test_migration_preserves_profiles_and_is_repeatable(tmp_path):
    old = tmp_path / "config.json"
    old.write_text('{"ui_language":"en","custom":9}')
    preview = tmp_path / "preview"
    preview.mkdir()
    settings = preview / "qt_settings.json"
    settings.write_text('{"ui_language":"uk","server_monitor":{"friends":["Player"],"servers":["example.com:12345"]}}')
    dest = migrate(old, preview)
    data = json.loads(dest.read_text())
    assert data == dict(custom=9, **json.loads(settings.read_text()))
    assert (tmp_path / "before-1.22" / "preview-settings.json").read_bytes() == settings.read_bytes()
    dest.write_text('{"custom":42}')
    assert migrate(old, preview).read_text() == '{"custom":42}'


@pytest.mark.parametrize("tag,draft,pre", [("v9.0.0",True,False),("v9.0.0",False,True),
    ("qt-preview-deadbeefabcd",False,False),("v9.0.0-rc1",False,False),("v1.17.4",False,False)])
def test_candidate_excludes_other_channels(tag,draft,pre):
    assert check_preview_release(lambda _: dict(tag_name=tag,draft=draft,prerelease=pre),
                                 installed=dict(channel="candidate",tag="v1.22.0")) is None


def test_signed_stable_installer_round_trip(tmp_path, monkeypatch):
    import base64
    import hashlib
    import io
    import update_client
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from qt_experiment.preview_updates import REPO, SUMS, download_preview, verify_installer
    tag = "v1.23.0"
    exe = "CoD2ChatTranslator_Setup.exe"
    root = f"https://github.com/{REPO}/releases/download/{tag}/"
    payload = b"MZ signed installer test fixture"
    digest = hashlib.sha256(payload).hexdigest()
    key = Ed25519PrivateKey.generate()
    encoded = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    monkeypatch.setattr(update_client, "UPDATE_SIGNING_PUBLIC_KEYS", {"fixture":base64.b64encode(encoded).decode()})
    manifest = dict(version=tag[1:],asset=exe,sha256=digest,signature_alg="ed25519",signature_key_id="fixture")
    manifest["signature"] = base64.b64encode(key.sign(update_client.update_signature_payload(manifest))).decode()
    release = dict(tag_name=tag, draft=False, prerelease=False, body="Fixes", assets=[
        dict(name=n,browser_download_url=root+n) for n in (exe, SUMS,"installer-update.json")])
    def getter(url):
        return manifest if url == root+"installer-update.json" else release
    installed = dict(channel="stable",tag="v1.22.0")
    candidate = check_preview_release(getter,installed)
    def opener(url):
        return io.BytesIO((digest+"  "+exe).encode() if url.endswith(SUMS) else payload)
    package = download_preview(candidate,tmp_path,opener)
    assert verify_installer(package,tmp_path).read_bytes() == payload
    with pytest.raises(RuntimeError):
        download_preview(candidate,tmp_path,opener,cancelled=lambda:True)
    with pytest.raises(ValueError):
        download_preview(candidate,tmp_path,lambda url: opener(url) if url.endswith(SUMS) else io.BytesIO(b"bad"))
    manifest["sha256"] = "0"*64
    with pytest.raises(ValueError,match="signed"):
        check_preview_release(getter,installed)


def test_experience_merge_uses_wal_and_does_not_duplicate(tmp_path):
    import sqlite3
    from contextlib import closing
    from translation_memory import initialize_schema
    preview = tmp_path / "preview"
    preview.mkdir()
    for folder, count in [(tmp_path, 2), (preview, 5)]:
        with closing(sqlite3.connect(folder / "translation_experience.sqlite3")) as db:
            initialize_schema(db)
            db.execute("INSERT INTO observations VALUES(NULL,'incoming','auto','ru','live','hello','привет','ok','local',0,'[]',1,?)",(count,))
            db.commit()
    with closing(sqlite3.connect(preview / "translation_experience.sqlite3")) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("UPDATE observations SET count=count+1")
        writer.commit()
        writer.execute("UPDATE observations SET count=99")
        for _ in range(2):
            migrate(tmp_path / "config.json", preview)
        with closing(sqlite3.connect(tmp_path / "translation_experience.sqlite3")) as db:
            assert db.execute("SELECT count FROM observations").fetchall() == [(8,)]
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
