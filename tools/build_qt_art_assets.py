"""Prepare approved generated component art for Qt nine-slice rendering.

Sources are committed in assets/qt_art/source; runtime only loads the small
processed PNGs in qt_experiment/art. Run this script after changing sources.
"""
from pathlib import Path
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/qt_art/source"
OUT = ROOT / "qt_experiment/art"
OUT.mkdir(parents=True, exist_ok=True)


def prepare(name, width, height, states=()):
    img = Image.open(SRC / (name + ".png")).convert("RGBA")
    alpha = img.getchannel("A")
    bounds = alpha.point(lambda a: 255 if a > 12 else 0).getbbox()
    if bounds:
        img = img.crop(bounds)
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(OUT / (name + ".png"), optimize=True)
    for state, brightness, saturation, opacity in states:
        rgb = Image.merge("RGB", img.split()[:3])
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
        a = img.getchannel("A").point(lambda x: round(x * opacity))
        rgb.putalpha(a)
        rgb.save(OUT / (name + "_" + state + ".png"), optimize=True)


prepare("frame", 600, 190)
states = (("hover", 1.15, 1.1, 1), ("pressed", .78, 1.15, 1),
          ("focused", 1.12, 1.15, 1), ("disabled", .65, .35, .63))
prepare("metal_button", 400, 90, states)
prepare("amber_button", 400, 90, states)
prepare("keycap", 240, 240, states)
