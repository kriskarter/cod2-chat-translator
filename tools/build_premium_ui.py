"""Rebuild the illustrated UI components from the project's source artwork.

Source PNGs are original project artwork.  The nine-slice button borders are
kept at their source size so Windows can stretch the middle without blurring
the machined corners.  No labels or live values are burned into any image.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "ui_premium"
OUT = ROOT / "assets" / "ui_wwii"


def material(width, height, *, start=0):
    steel = Image.open(SRC / "steel_source.png").convert("RGB")
    # Assemble from an authentic illustrated texture, keeping the display
    # materials consistent across the headers, buttons and footer.
    result = Image.new("RGB", (width, height))
    for x in range(0, width, steel.width):
        for y in range(0, height, steel.height):
            result.paste(steel, (x - start, y - start))
    return result


def button(name, *, amber=False, hover=False, pressed=False, disabled=False):
    w, h = 240, 58
    im = material(w, h, start=37).convert("RGBA")
    if amber:
        wash = (138, 55, 5, 175 if not hover else 205)
    elif hover:
        wash = (92, 66, 36, 105)
    else:
        wash = (24, 21, 17, 78)
    tint = Image.new("RGBA", im.size, wash)
    im = Image.alpha_composite(im, tint)
    if disabled:
        im = ImageEnhance.Contrast(im).enhance(.55)
    draw = ImageDraw.Draw(im, "RGBA")
    rim = (255, 187, 91, 235) if amber else (183, 151, 101, 228)
    if pressed:
        rim = (155, 96, 37, 210)
    draw.rounded_rectangle((1, 1, w - 2, h - 2), radius=7,
                           outline=(9, 8, 6, 255), width=2)
    draw.rounded_rectangle((3, 3, w - 4, h - 4), radius=6,
                           outline=rim, width=2)
    draw.line((11, 7, w - 12, 7), fill=(255, 226, 167, 95 if not pressed else 30), width=2)
    draw.line((11, h - 8, w - 12, h - 8), fill=(0, 0, 0, 190), width=3)
    for x in (12, w - 13):
        draw.ellipse((x - 2, h // 2 - 2, x + 2, h // 2 + 2),
                     fill=(10, 9, 7, 220), outline=(195, 155, 98, 190))
    im.save(OUT / f"premium_{name}.png", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hero = Image.open(SRC / "hero_source.png").convert("RGB")
    hero = hero.resize((1500, 500), Image.Resampling.LANCZOS)
    hero.crop((0, 17, 1500, 173)).save(OUT / "premium_hero.png", optimize=True)
    hero.crop((880, 55, 1470, 355)).resize((190, 86), Image.Resampling.LANCZOS).save(
        OUT / "premium_server.png", optimize=True)
    hero.crop((1080, 80, 1440, 350)).resize((94, 72), Image.Resampling.LANCZOS).save(
        OUT / "premium_overlay_preview.png", optimize=True)

    logo = Image.open(SRC / "logo_source.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo.thumbnail((580, 110), Image.Resampling.LANCZOS)
    logo.save(OUT / "premium_logo.png", optimize=True)

    plate = material(1024, 46, start=172).convert("RGBA")
    plate = Image.alpha_composite(plate, Image.new("RGBA", plate.size, (35, 28, 17, 55)))
    d = ImageDraw.Draw(plate, "RGBA")
    d.line((0, 0, 1024, 0), fill=(235, 192, 126, 210), width=2)
    d.line((0, 43, 1024, 43), fill=(11, 9, 6, 250), width=2)
    d.line((0, 45, 1024, 45), fill=(171, 132, 79, 195), width=1)
    plate.save(OUT / "premium_plate.png", optimize=True)

    for group, amber in (("metal", False), ("amber", True)):
        for state in ("normal", "hover", "pressed", "disabled"):
            button(f"{group}_{state}", amber=amber, hover=state == "hover",
                   pressed=state == "pressed", disabled=state == "disabled")
    # Distinct, true switch images; their state is controlled by Tk BooleanVar.
    for on in (False, True):
        im = material(52, 24, start=71).convert("RGBA")
        im = Image.alpha_composite(im, Image.new("RGBA", im.size,
                                    (107, 53, 5, 173) if on else (10, 10, 8, 180)))
        d = ImageDraw.Draw(im, "RGBA")
        d.rounded_rectangle((0, 1, 51, 23), radius=11,
                            outline=(242, 162, 56, 255) if on else (144, 118, 77, 255), width=2)
        x = 36 if on else 12
        d.ellipse((x - 9, 3, x + 9, 21), fill=(230, 210, 165, 255),
                  outline=(69, 44, 19, 255), width=2)
        im.save(OUT / f"premium_switch_{'on' if on else 'off'}.png", optimize=True)
    print("Premium art rebuilt from the three supplied original source images")


if __name__ == "__main__":
    main()
