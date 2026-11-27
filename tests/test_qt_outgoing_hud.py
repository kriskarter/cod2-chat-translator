"""Portable F9 editor rendering, monitor geometry and settings persistence."""
import pytest
from qt_experiment.outgoing_hud import outgoing_config, positioned, render_editor


def test_geometry_independent_and_monitor_relative():
    cfg = outgoing_config({"x": 9000, "y": 9000, "width": 720, "height": 200,
                           "font_size": 20, "background_opacity": .6})
    actual = positioned(cfg, (-1920, -100, 1366, 768))
    assert actual["x"] == -1920+1366-720
    assert actual["y"] == -100+768-200
    assert actual["font_size"] == 20
    assert actual["background_opacity"] == .6
    assert cfg["x"] == 9000
    assert outgoing_config({"width": "nan", "height": -1})["width"] == 720


def test_real_shared_renderer_and_auto_height():
    cfg = positioned({"width":500,"height":145,"font_size":14}, (0,0,1366,768))
    cfg["route"] = "RU → EN"
    image = render_editor("Привет! "*60,"Hello! "*60,"Enter — отправить · Esc — отменить",cfg)
    assert image.mode == "RGBA"
    assert image.width == 500
    assert 145 <= image.height <= cfg["max_render_height"]
    fixed = dict(cfg, auto_height=False)
    assert render_editor("Привет","Hello","Enter",fixed).size == (500,145)


def test_outgoing_settings_roundtrip_without_changing_incoming(tmp_path):
    pytest.importorskip("PySide6")
    from PySide6.QtGui import QGuiApplication
    from qt_experiment.translation_runtime import TranslationState, read_translation_config
    from qt_experiment.settings_store import SettingsStore
    app = QGuiApplication.instance() or QGuiApplication([])
    path = tmp_path/"qt_settings.json"
    store = SettingsStore(path)
    defaults = read_translation_config(None)
    state = TranslationState(store.load(defaults), settings_store=store)
    old = dict(state._hud.config)
    try:
        assert state.applyOutgoingHud({"width":880,"height":240,"font_size":17,"x":90,"y":120,"background_opacity":.7})
        assert state._hud.config == old
        assert state.outgoingHudSettings["width"] == 880
        assert state.outgoingHudPreview(state.outgoingHudSettings).startswith("data:image/png;base64,")
        saved = SettingsStore(path).load(defaults)
        assert saved["outgoing_hud"]["x"] == 90
        assert saved["outgoing_hud"]["font_size"] == 17
        assert saved["outgoing_hud"]["background_opacity"] == .7
        assert saved["overlay"] == old
    finally:
        state.stop()
