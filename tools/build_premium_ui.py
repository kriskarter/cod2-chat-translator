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
    # A small source tile is essential: ttk must size controls from their
    # actual caption, not inherit a giant bitmap's natural width/height.
    w, h = 64, 36
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
    im.save(OUT / f"premium_{name}.png", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hero = Image.open(SRC / "hero_source.png").convert("RGB")
    hero = hero.resize((1500, 500), Image.Resampling.LANCZOS)
    # Keep a taller composition so the helmet, skyline and stonework remain
    # legible behind the separate logo at the real 148px Windows header.
    hero.crop((0, 0, 1500, 180)).save(OUT / "premium_hero.png", optimize=True)
    hero.crop((880, 55, 1470, 355)).resize((190, 86), Image.Resampling.LANCZOS).save(
        OUT / "premium_server.png", optimize=True)
    hero.crop((1080, 80, 1440, 350)).resize((94, 72), Image.Resampling.LANCZOS).save(
        OUT / "premium_overlay_preview.png", optimize=True)

    logo = Image.open(SRC / "logo_source.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo.thumbnail((640, 136), Image.Resampling.LANCZOS)
    logo.save(OUT / "premium_logo.png", optimize=True)
    logo.thumbnail((580, 120), Image.Resampling.LANCZOS)
    logo.save(OUT / "premium_logo_compact.png", optimize=True)

    plate = material(1024, 46, start=172).convert("RGBA")
    plate = Image.alpha_composite(plate, Image.new("RGBA", plate.size, (35, 28, 17, 55)))
    d = ImageDraw.Draw(plate, "RGBA")
    d.line((0, 0, 1024, 0), fill=(235, 192, 126, 210), width=2)
    d.line((0, 43, 1024, 43), fill=(11, 9, 6, 250), width=2)
    d.line((0, 45, 1024, 45), fill=(171, 132, 79, 195), width=1)
    plate.save(OUT / "premium_plate.png", optimize=True)

    # Keep the corners/edges of the approved new material independent of
    # destination width or height. ttk stretches only the neutral center.
    panel = Image.open(SRC / "generic_panel.png").convert("RGBA")
    tile = Image.new("RGBA", (160, 160))
    source = 126
    border = 42
    for dest_y, src_y, dest_h, src_h in (
        (0, 0, border, source),
        (border, panel.height//2-32, 76, 64),
        (118, panel.height-source, border, source),
    ):
        for dest_x, src_x, dest_w, src_w in (
            (0, 0, border, source),
            (border, panel.width//2-32, 76, 64),
            (118, panel.width-source, border, source),
        ):
            cut=panel.crop((src_x,src_y,src_x+src_w,src_y+src_h))
            tile.alpha_composite(cut.resize((dest_w,dest_h),Image.Resampling.LANCZOS),
                                 (dest_x,dest_y))
    tile.save(OUT / "premium_generic_frame.png", optimize=True)

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
        check = material(22, 22, start=43).convert("RGBA")
        check = Image.alpha_composite(check, Image.new("RGBA", check.size,
             (138, 64, 4, 200) if on else (11, 10, 8, 200)))
        c = ImageDraw.Draw(check, "RGBA")
        c.rounded_rectangle((1, 1, 20, 20), radius=3,
            outline=(255, 177, 72, 255) if on else (172, 146, 99, 255), width=2)
        if on:
            c.line((5, 11, 9, 15, 17, 6), fill=(255, 240, 197, 255), width=3,
                   joint="curve")
        check.save(OUT / f"premium_check_{'on' if on else 'off'}.png", optimize=True)

    trough = material(100, 13, start=93).convert("RGBA")
    trough = Image.alpha_composite(trough, Image.new("RGBA", trough.size,
                                                    (10, 9, 6, 195)))
    t = ImageDraw.Draw(trough, "RGBA")
    t.rounded_rectangle((1, 3, 98, 10), radius=3, fill=(32, 24, 15, 255),
                        outline=(158, 125, 76, 255), width=1)
    t.line((5, 5, 94, 5), fill=(240, 165, 62, 145), width=2)
    trough.save(OUT / "premium_scale_trough.png", optimize=True)
    thumb = material(22, 26, start=99).convert("RGBA")
    th = ImageDraw.Draw(thumb, "RGBA")
    th.rounded_rectangle((2, 2, 19, 23), radius=6, fill=(188, 159, 108, 255),
                         outline=(245, 211, 145, 255), width=2)
    th.line((7, 9, 14, 9), fill=(88, 64, 37, 255), width=2)
    th.line((7, 16, 14, 16), fill=(88, 64, 37, 255), width=2)
    thumb.save(OUT / "premium_scale_thumb.png", optimize=True)
    print("Premium art rebuilt from the three supplied original source images")


if __name__ == "__main__":
    main()
