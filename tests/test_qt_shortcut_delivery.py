"""Exercise the registered Windows callback and Qt drain without sending OS input."""
import ctypes
import os
import queue
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
pytest.importorskip("PySide6")


@pytest.mark.skipif(os.name != "nt", reason="Win32 callback ABI")
def test_registered_callback_delivers_scoped_shortcuts_and_no_plain_keys():
    from ctypes import wintypes
    from qt_experiment.game_controls import GameControls
    from qt_experiment.native_hud import NativeHud

    class Key(ctypes.Structure):
        _fields_ = [(n,wintypes.DWORD) for n in ("vk","scan","flags","stamp")]+[("extra",ctypes.c_size_t)]

    focused = [False]
    state = SimpleNamespace(f9=True, game_status=Mock(), toggle=Mock(), capture_game_screenshot=Mock(),
                            position_outgoing_hud=Mock())
    game = GameControls(state, {}, "ru","en",foreground=lambda:focused[0],
                        hud_factory=lambda cfg,orig:NativeHud(cfg,orig,factory=Mock))
    kb = game.keyboard
    kb.shortcut_trace = queue.SimpleQueue()
    try:
        kb.start()
        assert game.events.get(timeout=5)[0] == "hook_ready"
        def press(vk):
            data=Key(vk,0,0x10,0,0)
            for msg in (0x100,0x101):
                kb.callback(0,msg,ctypes.addressof(data))
        press(0x77)
        game.tick()
        state.toggle.assert_not_called()
        press(0x41)
        focused[0]=True
        for vk in (0x77,0x79,0x78): press(vk)
        game.tick()
        state.toggle.assert_called_once_with("overlay")
        state.capture_game_screenshot.assert_called_once()
        assert game.active and game.last_shortcut=="F9"
        recorded=[kb.shortcut_trace.get_nowait()[1:4] for _ in range(4)]
        assert recorded==[(0x77,True,False),(0x77,True,True),(0x79,True,True),(0x78,True,True)]
        assert kb.shortcut_trace.empty()
    finally:
        game.close()
        kb._thread.join(5)


def test_poll_only_reads_three_keys_and_suppresses_seen_hook_edges():
    from qt_experiment.shortcut_diagnostics import ShortcutDiagnostics
    diag = ShortcutDiagnostics.__new__(ShortcutDiagnostics)
    down = {0x77,0x78,0x79}
    def read(vk):
        assert vk in (0x77,0x78,0x79)
        return 0x8000 if vk in down else 0
    diag.user = SimpleNamespace(GetAsyncKeyState=read)
    diag.down = set()
    kb = SimpleNamespace(shortcut_held={0x78},shortcut_at={0x79:99.99})
    assert list(diag.missed(kb,100)) == ["f8"]
    assert list(diag.missed(kb,101)) == []
    down.clear()
    assert list(diag.missed(kb,102)) == []
    down.add(0x79)
    assert list(diag.missed(kb,103)) == ["screenshot"]
