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


def test_real_qml_preview_dialog(tmp_path):
    import os
    from pathlib import Path
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QUrl, QObject
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtTest import QTest
    from qt_experiment.common import ROOT
    from qt_experiment.translation_runtime import TranslationState, read_translation_config
    app = QGuiApplication.instance() or QGuiApplication([])
    state = TranslationState(read_translation_config(None))
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(i.toString() for i in items))
    engine.rootContext().setContextProperty("prototype",state)
    engine.load(QUrl.fromLocalFile(str(ROOT/"qt_experiment/Home.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]
    try:
        window.resize(1342,672)
        window.setProperty("activePage","outgoing")
        QTest.qWait(100)
        window.setProperty("evidenceDialog","outgoing_hud_dialog")
        QTest.qWait(350)
        preview = window.findChild(QObject,"outgoingHudPreview")
        assert preview is not None
        assert preview.property("sourceSize").width() > 0
        assert not warnings, warnings
        capture=os.environ.get("COD2_QT_TEST_SCREENSHOTS")
        if capture:
            assert window.grabWindow().save(str(Path(capture)/"outgoing_hud_settings.png"))
            import base64
            data=state.outgoingHudPreview(state.outgoingHudSettings).split(",",1)[1]
            (Path(capture)/"outgoing_hud_renderer.png").write_bytes(base64.b64decode(data))
    finally:
        window.close()
        del engine
        state.stop()


def test_renderer_wraps_long_tokens_and_retains_words():
    from PIL import Image, ImageDraw
    from qt_experiment.outgoing_hud import wrap, font
    face = font(14)
    draw = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    text = "Слово " + "a"*150 + " конец"
    lines = wrap(draw,text,face,100)
    assert all(draw.textlength(line,font=face)<=100 for line in lines)
    assert "".join(lines).replace(" ","") == text.replace(" ","")


def test_native_renderer_comparison_evidence():
    import os
    if os.name != "nt":
        pytest.skip("Windows renderer comparison")
    import json
    import time
    import statistics
    from pathlib import Path
    from app import OverlayItem
    from win32_layered_overlay import build_image
    cfg = positioned({"width":720,"height":200,"x":0,"y":0}, (0,0,1366,768))
    text = "Привет, прикрой меня у моста!"
    translation = "Hey, cover me at the bridge!"
    item = OverlayItem("Enter — отправить · Esc — отменить",text,translation,time.monotonic())
    results = {}
    for name, render in (("legacy_generic",lambda:build_image([item],cfg,True)),
                         ("outgoing_editor",lambda:render_editor(text,translation,item.nickname,cfg))):
        render()
        samples=[]
        for i in range(20):
            start=time.perf_counter()
            render()
            samples.append((time.perf_counter()-start)*1000)
        results[name]={"median_ms":round(statistics.median(samples),3),"p95_ms":round(sorted(samples)[18],3)}
    capture = os.environ.get("COD2_QT_TEST_SCREENSHOTS")
    if capture:
        (Path(capture)/"f9_renderer_benchmark.json").write_text(json.dumps({
            "scenario":"Windows image rendering only, not Win32 presentation, gameplay or network latency",
            **results},indent=2),encoding="utf-8")
