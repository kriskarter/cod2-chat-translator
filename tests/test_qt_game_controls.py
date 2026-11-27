"""Qt game controls: scoped hook, cancellation and verified translation handoff."""
import os
import time
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

pytest.importorskip("PySide6")
from qt_experiment.game_controls import GameControls
from qt_experiment.native_hud import NativeHud


class Keyboard:
    def __init__(self, events, game_scope):
        self.events, self.game_scope = events, game_scope
        self.active = False
    def set_enabled(self, enabled):
        if not enabled:
            self.active = False
    def set_active(self, value): self.active = value
    def start(self): pass
    def stop(self): self.active = False


def wait(game, predicate):
    end = time.monotonic() + 3
    while time.monotonic() < end:
        game.tick()
        if predicate():
            return
        time.sleep(.01)
    assert predicate()


def test_game_actions_and_cancel_stale_result():
    focused = [False]
    state = SimpleNamespace(record_sent=Mock(), show_f8_notice=Mock(), translationChanged=Mock(), f9=True, _f8_settings=("ru", True, True, "live", True, True),
                            position_outgoing_hud=Mock(), game_status=Mock(), toggle=Mock(), capture_game_screenshot=Mock())
    surface = Mock()
    sender = Mock(return_value=(True, ""))
    translator = Mock(return_value="cover me")
    game = GameControls(state, {}, "ru", "en", foreground=lambda: focused[0],
                        keyboard_factory=Keyboard, hud_factory=lambda cfg, original: NativeHud(cfg, original, factory=lambda: surface),
                        translator=translator, sender=sender)
    try:
        game.events.put(("toggle_popup", None))
        game.tick()
        assert not game.active
        focused[0] = True
        game.events.put(("f8", None))
        game.events.put(("screenshot", None))
        game.events.put(("toggle_popup", None))
        game.events.put(("text", "прикрой меня"))
        game.tick()
        state.toggle.assert_called_once_with("f8")
        state.capture_game_screenshot.assert_called_once()
        assert game.active and game.keyboard.active
        game.events.put(("submit", None))
        game.tick()
        old_id = game.generation
        focused[0] = False
        game.tick()
        assert not game.active and not game.keyboard.active
        game.events.put(("result", (old_id, True, "cover me")))
        game.tick()
        sender.assert_not_called()
        focused[0] = True
        game.events.put(("toggle_popup", None))
        game.events.put(("text", "прикрой меня"))
        game.events.put(("submit", None))
        wait(game, lambda: sender.called and not game.sending)
        sender.assert_called_once_with("cover me")
        assert not game.keyboard.active
    finally:
        game.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows hook")
def test_native_keyboard_hook_starts_and_stops():
    import queue
    from outgoing_chat import KeyboardCapture
    events = queue.Queue()
    hook = KeyboardCapture(events, game_scope=lambda: False)
    try:
        hook.start()
        event, detail = events.get(timeout=5)
        assert event == "hook_ready", detail
    finally:
        hook.stop()
        if hook._thread:
            hook._thread.join(5)
    assert not hook._thread.is_alive()


def test_live_preview_never_sends_until_enter():
    state = SimpleNamespace(record_sent=Mock(), show_f8_notice=Mock(), translationChanged=Mock(), f9=True, _f8_settings=("ru", True, True, "live", True, True),
                            position_outgoing_hud=Mock(), game_status=Mock(), toggle=Mock(), capture_game_screenshot=Mock())
    surface = Mock()
    sender = Mock(return_value=(True, ""))
    translator = Mock(return_value="cover me")
    game = GameControls(state, {}, "ru", "en", foreground=lambda: True,
                        keyboard_factory=Keyboard, hud_factory=lambda cfg, original: NativeHud(cfg, original, factory=lambda: surface),
                        translator=translator, sender=sender)
    try:
        game.events.put(("toggle_popup", None))
        game.events.put(("text", "прикрой меня"))
        wait(game, lambda: game.preview_result == "cover me")
        assert game.hud.items[0].translated == "cover me"
        sender.assert_not_called()
        game.events.put(("submit", None))
        wait(game, lambda: sender.called and not game.sending)
        sender.assert_called_once_with("cover me")
        translator.assert_called_once()
    finally:
        game.close()


def test_foreground_gate_accepts_all_supported_client_names(monkeypatch):
    import outgoing_send
    from server_catalog import MULTIPLAYER_EXECUTABLES
    for image in (*MULTIPLAYER_EXECUTABLES, "cod2.exe", "notepad.exe", "", "cod2mp_s.exe.bak"):
        monkeypatch.setattr(outgoing_send, "foreground_process_name", lambda: image.casefold())
        assert outgoing_send.is_cod2_foreground() == (image in (*MULTIPLAYER_EXECUTABLES, "cod2.exe"))


def test_screenshot_discards_capture_when_window_changes(monkeypatch,tmp_path):
    import queue
    import outgoing_send
    from PIL import ImageGrab, Image
    from qt_experiment.translation_runtime import TranslationState
    window=Mock()
    window.GetForegroundWindow.side_effect=(41,41,42)
    monkeypatch.setattr(outgoing_send,"_foreground_api",lambda:(window,None))
    monkeypatch.setattr(outgoing_send,"is_cod2_foreground",lambda:True)
    grab=Mock(return_value=Image.new("RGB",(8,8),"white"))
    monkeypatch.setattr(ImageGrab,"grab",grab)
    state=SimpleNamespace(ui_queue=queue.Queue(),_screenshot_directory=lambda:tmp_path)
    TranslationState._capture_game_screenshot_worker(state)
    grab.assert_called_once_with(window=41)
    assert state.ui_queue.get_nowait()[0]=="screenshot_error"
    assert not list(tmp_path.iterdir())


def test_failed_send_restores_draft_and_requires_new_submit():
    state = SimpleNamespace(record_sent=Mock(), show_f8_notice=Mock(), translationChanged=Mock(), f9=True, _f8_settings=("ru", True, True, "live", True, True),
                            position_outgoing_hud=Mock(), game_status=Mock())
    sender = Mock(side_effect=[(False,"send failed"),(True,"")])
    game = GameControls(state, {}, "ru", "en", foreground=lambda: True,
                        keyboard_factory=Keyboard, hud_factory=lambda cfg, orig: NativeHud(cfg,orig,factory=Mock),
                        translator=Mock(return_value="hello"), sender=sender)
    try:
        game.open()
        game.events.put(("text", "привет"))
        wait(game, lambda: game.preview_result == "hello")
        game.submit()
        wait(game, lambda: game.active and not game.sending)
        assert game.buffer == "привет"
        assert sender.call_count == 1
        wait(game, lambda: game.preview_result == "hello")
        assert sender.call_count == 1
        game.submit()
        wait(game, lambda: not game.active and not game.sending)
        assert sender.call_count == 2
    finally:
        game.close()
