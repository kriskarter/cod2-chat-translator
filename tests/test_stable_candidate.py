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
