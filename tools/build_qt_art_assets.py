"""Bake static QML controls from the generated instrument-metal swatches."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/qt_art/source"
OUT = ROOT / "qt_experiment/art"
OUT.mkdir(exist_ok=True)
sheet = Image.open(SRC / "instrument_metals.jpg").convert("RGB")
STATES = {"": 1, "_hover": 1.12, "_pressed": .82, "_focused": 1.08, "_disabled": .68}


def face(band, size, low, high):
    w, h = sheet.size
    crop = sheet.crop((w // 10, (band + .10) * h / 3, w * .90, (band + .90) * h / 3))
    grain = ImageOps.autocontrast(ImageOps.grayscale(crop.resize(size)), cutoff=2)
    return ImageOps.colorize(grain, low, high)


def plate(name, band, low, high, edge):
    size = (144, 36)
    base = face(band, size, low, high)
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 143, 35), 5, fill=255)
    for suffix, brightness in STATES.items():
        im = base.copy()
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle((0, 0, 143, 35), 5, outline="#131512")
        draw.rounded_rectangle((1, 1, 142, 34), 4, outline=edge)
        draw.line((6, 2, 137, 2), fill=high)
        draw.line((5, 33, 138, 33), fill=low)
        im = ImageEnhance.Brightness(im).enhance(brightness)
        if suffix == "_disabled":
            im = ImageEnhance.Color(im).enhance(.25)
        im.putalpha(mask)
        im.save(OUT / f"{name}{suffix}.png", optimize=True)


plate("metal_button", 0, "#232521", "#4d4b40", "#746c59")
plate("amber_button", 1, "#614322", "#a77d40", "#bd995f")
face(2, (96, 28), "#1c291f", "#3d513a").save(OUT / "switch_face.png")
face(0, (96, 28), "#212522", "#3b403a").save(OUT / "switch_off.png")
frame = Image.new("RGBA", (64, 48))
d = ImageDraw.Draw(frame)
for i, color in enumerate(["#101310", "#766955", "#383c33"]):
    d.rounded_rectangle((i, i, 63-i, 47-i), radius=7-i, outline=color)
d.line((8, 1, 55, 1), fill="#9a896e")
frame.save(OUT / "frame.png")

key = Image.open(SRC / "keycap.png").convert("RGBA")
key = key.crop(key.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox())
key = key.resize((240, 240), Image.Resampling.LANCZOS)
for suffix, brightness in STATES.items():
    im = ImageEnhance.Color(key).enhance(.80)
    im = ImageEnhance.Brightness(im).enhance(brightness * .94)
    im.save(OUT / f"keycap{suffix}.png", optimize=True)
