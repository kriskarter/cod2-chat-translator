from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "source_icon.png"
SOURCE_B64 = ASSETS / "source_icon.b64"


def _font(size: int, bold: bool = False):
    candidates = []
    if os.name == "nt":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates += [
            windir / "Fonts" / ("segoeuib.ttf" if bold else "segoeui.ttf"),
            windir / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        ]
    candidates += [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def main() -> None:
    if not SOURCE.exists():
        if SOURCE_B64.exists():
            import base64
            SOURCE.write_bytes(base64.b64decode(SOURCE_B64.read_text(encoding="ascii")))
        else:
            raise SystemExit(f"Missing icon source: {SOURCE_B64}")
    base = Image.open(SOURCE).convert("RGBA")
    # normalize to square transparent canvas
    box = base.getbbox()
    if box:
        base = base.crop(box)
    side = max(base.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(base, ((side-base.width)//2, (side-base.height)//2))
    base = canvas

    for size in (32, 48, 64, 128, 256):
        base.resize((size, size), Image.Resampling.LANCZOS).save(ASSETS / f"app_{size}.png")

    base.resize((256, 256), Image.Resampling.LANCZOS).save(
        ASSETS / "app.ico", format="ICO",
        sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)]
    )

    # Inno Setup wizard artwork. 24-bit BMP keeps compatibility with Inno Setup.
    W, H = 164, 314
    wiz = Image.new("RGB", (W, H), (17, 31, 46))
    draw = ImageDraw.Draw(wiz)
    draw.rectangle([0, 0, W-1, 5], fill=(72, 153, 203))
    draw.rectangle([0, H-5, W-1, H-1], fill=(224, 153, 20))
    logo = base.resize((142, 142), Image.Resampling.LANCZOS)
    wiz.paste(logo, (11, 12), logo)
    draw.text((12, 178), "COD 2 Chat", font=_font(20, True), fill=(245,247,250))
    draw.text((12, 202), "Translator", font=_font(19, True), fill=(245,183,28))
    draw.text((12, 244), "Real-time chat", font=_font(12), fill=(218,225,233))
    draw.text((12, 261), "translation overlay", font=_font(12), fill=(218,225,233))
    wiz.save(ASSETS / "wizard.bmp", format="BMP")

    small = Image.new("RGB", (55, 55), (17, 31, 46))
    sm = base.resize((53, 53), Image.Resampling.LANCZOS)
    small.paste(sm, (1, 1), sm)
    small.save(ASSETS / "wizard_small.bmp", format="BMP")
    print("Generated Windows icon and installer artwork from assets/source_icon.png")


if __name__ == "__main__":
    main()
