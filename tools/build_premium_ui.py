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
        wash = (99, 72, 43, 152 if not hover else 177)
    elif hover:
        wash = (71, 77, 74, 95)
    else:
        wash = (26, 32, 36, 115)
    tint = Image.new("RGBA", im.size, wash)
    im = Image.alpha_composite(im, tint)
    if disabled:
        im = ImageEnhance.Contrast(im).enhance(.55)
    draw = ImageDraw.Draw(im, "RGBA")
    rim = (226, 177, 108, 213) if amber else (161, 150, 127, 210)
    if pressed:
        rim = (155, 96, 37, 210)
    draw.rounded_rectangle((1, 1, w - 2, h - 2), radius=7,
                           outline=(9, 12, 13, 240), width=1)
    draw.rounded_rectangle((3, 3, w - 4, h - 4), radius=6,
                           outline=rim, width=1)
    draw.line((11, 7, w - 12, 7), fill=(255, 226, 167, 95 if not pressed else 30), width=2)
    draw.line((11, h - 8, w - 12, h - 8), fill=(0, 0, 0, 190), width=3)
    im.save(OUT / f"premium_{name}.png", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Project-original illustrated key and signal icon. Live captions and
    # states are composed at runtime, not burned into the asset.
    for source, output, bounds in (
        ("keycap_source.png", "premium_keycap.png", (180, 180)),
        ("radio_source.png", "premium_radio.png", (42, 42)),
    ):
        artwork = Image.open(SRC / source).convert("RGBA")
        artwork.thumbnail(bounds, Image.Resampling.LANCZOS)
        artwork.save(OUT / output, optimize=True)
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
    plate = Image.alpha_composite(plate, Image.new("RGBA", plate.size, (30, 36, 38, 115)))
    d = ImageDraw.Draw(plate, "RGBA")
    d.line((0, 0, 1024, 0), fill=(235, 192, 126, 210), width=2)
    d.line((0, 43, 1024, 43), fill=(11, 9, 6, 250), width=2)
    d.line((0, 45, 1024, 45), fill=(171, 132, 79, 195), width=1)
    plate.save(OUT / "premium_plate.png", optimize=True)

    # Navigation is a single continuous metal bar. Individual controls have
    # no enclosing button outline; selection is a soft amber wash.
    for state in ("normal", "hover", "active", "pressed"):
        nav = material(64, 40, start=84).convert("RGBA")
        glow = {"normal": (22, 27, 30, 185), "hover": (61, 62, 54, 155),
                "active": (78, 66, 48, 153), "pressed": (88, 65, 39, 173)}[state]
        nav = Image.alpha_composite(nav, Image.new("RGBA", nav.size, glow))
        if state != "normal":
            sheen=Image.new("RGBA",nav.size)
            bands=ImageDraw.Draw(sheen,"RGBA")
            for y in range(40):
                alpha=round((30 if state=="hover" else 58)*max(0,1-abs(y-17)/23))
                bands.line((0,y,64,y),fill=(229,149,62,alpha))
            nav=Image.alpha_composite(nav,sheen)
        d = ImageDraw.Draw(nav, "RGBA")
        d.line((0, 0, 64, 0), fill=(192, 155, 103, 140), width=1)
        d.line((0, 39, 64, 39), fill=(15, 12, 8, 255), width=2)
        if state != "normal":
            d.line((5, 36, 59, 36), fill=(247, 177, 68, 175 if state=="active" else 95), width=2)
        nav.save(OUT / f"premium_nav_{state}.png", optimize=True)

    chip = Image.new("RGBA", (28, 28))
    chip_draw = ImageDraw.Draw(chip)
    gold = (228, 190, 116, 245)
    chip_draw.rounded_rectangle((7, 7, 21, 21), radius=2, outline=gold, width=2)
    chip_draw.rectangle((11, 11, 17, 17), fill=(133, 164, 118, 230))
    for coord in (10, 14, 18):
        chip_draw.line((coord, 3, coord, 7), fill=gold, width=2)
        chip_draw.line((coord, 21, coord, 25), fill=gold, width=2)
        chip_draw.line((3, coord, 7, coord), fill=gold, width=2)
        chip_draw.line((21, coord, 25, coord), fill=gold, width=2)
    chip.save(OUT / "premium_chip.png", optimize=True)
    chip.resize((36, 36), Image.Resampling.LANCZOS).save(
        OUT / "premium_chip_rail.png", optimize=True)

    # Footer symbols have their own size; enlarging a tiny widget photo in
    # Tk would lose the edges and shift the neighboring live captions.
    hud = Image.new("RGBA", (36, 36))
    hd = ImageDraw.Draw(hud, "RGBA")
    hd.line((5, 13, 18, 4, 31, 13, 18, 22, 5, 13),
            fill=(238, 207, 147, 240), width=3, joint="curve")
    hd.line((5, 19, 18, 28, 31, 19), fill=(166, 137, 95, 230),
            width=3, joint="curve")
    hd.line((5, 25, 18, 34, 31, 25), fill=(116, 146, 119, 220),
            width=2, joint="curve")
    hud.save(OUT / "premium_overlay_rail.png", optimize=True)

    # Distinct plus pictogram for the actual add-server action.
    add = Image.new("RGBA", (22, 22))
    add_draw = ImageDraw.Draw(add)
    add_draw.rounded_rectangle((2, 2, 19, 19), radius=4,
                               outline=(210, 176, 116, 235), width=2)
    add_draw.line((11, 6, 11, 15), fill=(250, 221, 161, 255), width=2)
    add_draw.line((6, 11, 15, 11), fill=(250, 221, 161, 255), width=2)
    add.save(OUT / "quick_add.png", optimize=True)
    star = Image.new("RGBA", (22, 22))
    sd = ImageDraw.Draw(star)
    from math import cos, pi, sin
    outline=[]
    for index in range(10):
        angle=-pi/2+index*pi/5
        radius=10 if index%2==0 else 4.4
        outline.append((round(11+cos(angle)*radius),
                        round(11+sin(angle)*radius)))
    sd.polygon(outline,fill=(217,169,92,230))
    sd.line(outline+[outline[0]],fill=(255,226,163,245),width=1)
    star.save(OUT / "quick_star.png",optimize=True)
    friends = Image.new("RGBA", (28, 28))
    fd = ImageDraw.Draw(friends)
    fd.ellipse((3, 4, 12, 13), fill=(171, 195, 149, 240))
    fd.ellipse((16, 4, 25, 13), fill=(171, 195, 149, 240))
    fd.rounded_rectangle((1, 16, 13, 25), radius=4,
                         fill=(99, 143, 105, 235), outline=gold)
    fd.rounded_rectangle((15, 16, 27, 25), radius=4,
                         fill=(99, 143, 105, 235), outline=gold)
    friends.save(OUT / "quick_friends.png", optimize=True)

    # A subdued selection wash for the real Treeview cells.  The ttk cell
    # element stretches this strip; captions and server values stay live.
    selection = Image.new("RGBA", (120, 29))
    sd = ImageDraw.Draw(selection, "RGBA")
    for y in range(29):
        distance = abs(y - 12) / 17
        sd.line((0, y, 119, y), fill=(87, 69, 43, round(185 - 65 * distance)))
    sd.line((0, 0, 119, 0), fill=(202, 153, 82, 125), width=1)
    sd.line((0, 28, 119, 28), fill=(16, 18, 17, 205), width=1)
    selection.save(OUT / "premium_selection.png", optimize=True)
    Image.new("RGBA", (120, 29)).save(OUT / "premium_selection_clear.png", optimize=True)

    for name in ("servers", "history", "translation", "overlay"):
        icon = Image.new("RGBA", (28, 28))
        i = ImageDraw.Draw(icon, "RGBA")
        gold=(228, 189, 116, 255)
        if name == "servers":
            for top in (5, 13):
                i.rounded_rectangle((3, top, 24, top+6), radius=2,
                                    outline=gold, width=2)
                i.ellipse((6, top+2, 8, top+4), fill=gold)
        elif name == "history":
            for x, top in ((5, 15), (12, 9), (19, 4)):
                i.rounded_rectangle((x, top, x+4, 23), radius=1, fill=gold)
            i.line((3, 24, 25, 24), fill=gold, width=1)
        elif name == "translation":
            i.rounded_rectangle((3, 5, 17, 17), radius=2, outline=gold, width=2)
            i.line((6, 20, 6, 17, 10, 17), fill=gold, width=2)
            i.line((11, 9, 22, 9), fill=gold, width=2)
            i.line((17, 7, 17, 14), fill=gold, width=2)
            i.line((13, 21, 24, 21), fill=gold, width=2)
        else:
            i.rounded_rectangle((4, 8, 24, 20), radius=2, outline=gold, width=2)
            i.line((8, 5, 8, 8), fill=gold, width=2)
            i.line((20, 5, 20, 8), fill=gold, width=2)
            i.line((10, 15, 18, 15), fill=gold, width=2)
        icon.save(OUT / f"nav_{name}.png", optimize=True)

    # Keep the corners/edges of the approved new material independent of
    # destination width or height. ttk stretches only the neutral center.
    panel = Image.open(SRC / "generic_panel.png").convert("RGBA")
    panel = ImageEnhance.Color(panel).enhance(.6)
    panel = ImageEnhance.Brightness(panel).enhance(.86)
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
                                    (29, 89, 48, 176) if on else (18, 22, 22, 185)))
        d = ImageDraw.Draw(im, "RGBA")
        d.rounded_rectangle((0, 1, 51, 23), radius=11,
                            outline=(126, 223, 127, 255) if on else (116, 122, 113, 255), width=1)
        x = 36 if on else 12
        d.ellipse((x - 9, 3, x + 9, 21), fill=(211, 234, 192, 255) if on else (190, 191, 177, 255),
                  outline=(69, 44, 19, 255), width=2)
        im.save(OUT / f"premium_switch_{'on' if on else 'off'}.png", optimize=True)
        check = material(22, 22, start=43).convert("RGBA")
        check = Image.alpha_composite(check, Image.new("RGBA", check.size,
             (138, 64, 4, 200) if on else (11, 10, 8, 200)))
        c = ImageDraw.Draw(check, "RGBA")
        c.rounded_rectangle((1, 1, 20, 20), radius=3,
            outline=(118, 201, 129, 255) if on else (137, 141, 132, 255), width=1)
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
    # Small controls are nine-slice images, not Windows default scrollbars.
    track = material(14, 48).convert("RGBA")
    track = Image.alpha_composite(track, Image.new("RGBA", track.size, (19, 24, 26, 225)))
    d = ImageDraw.Draw(track, "RGBA")
    d.rounded_rectangle((1, 1, 12, 46), radius=4,
                        outline=(103, 95, 79, 235), width=1)
    track.save(OUT / "premium_scroll_track.png", optimize=True)
    grip = material(14, 42).convert("RGBA")
    grip = Image.alpha_composite(grip, Image.new("RGBA", grip.size, (62, 66, 63, 185)))
    d = ImageDraw.Draw(grip, "RGBA")
    d.rounded_rectangle((1, 1, 12, 40), radius=4,
                        outline=(200, 164, 112, 235), width=1)
    for y in (18, 21, 24):
        d.line((4, y, 9, y), fill=(233, 207, 161, 160), width=1)
    grip.save(OUT / "premium_scroll_grip.png", optimize=True)
    arrow = material(24, 24).convert("RGBA")
    arrow = Image.alpha_composite(arrow, Image.new("RGBA", arrow.size, (36, 29, 19, 205)))
    d = ImageDraw.Draw(arrow, "RGBA")
    d.line((0, 0, 0, 23), fill=(165, 122, 68, 230), width=2)
    d.polygon(((6, 9), (18, 9), (12, 16)), fill=(240, 190, 112, 255))
    arrow.save(OUT / "premium_combo_arrow.png", optimize=True)
    print("Premium art rebuilt from the three supplied original source images")


if __name__ == "__main__":
    main()
