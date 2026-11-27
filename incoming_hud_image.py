"""Incoming HUD pixels shared by the Win32 surface and the placement editor."""
import os
from PIL import Image, ImageDraw, ImageFont

_FONT_CACHE = {}


def _font(size: int, bold: bool = False):
    px = max(8, round(int(size) * 1.15))
    key = (px, bool(bold))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = os.path.join(
        os.environ.get("WINDIR", r"C:\Windows"),
        "Fonts",
        name,
    )
    try:
        value = ImageFont.truetype(path, px)
    except Exception:
        value = ImageFont.load_default()
    _FONT_CACHE[key] = value
    return value


def _measure(draw, text, font, stroke_width):
    box = draw.textbbox(
        (0, 0),
        text or " ",
        font=font,
        stroke_width=stroke_width,
    )
    return max(1, box[2] - box[0]), max(1, box[3] - box[1])


def _wrap(draw, text, font, max_width, stroke_width):
    text = " ".join(str(text or "").split())
    if not text:
        return [""]

    lines = []
    current = ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if _measure(draw, candidate, font, stroke_width)[0] <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = ""

        if _measure(draw, word, font, stroke_width)[0] <= max_width:
            current = word
            continue

        chunk = ""
        for char in word:
            candidate = chunk + char
            if chunk and _measure(draw, candidate, font, stroke_width)[0] > max_width:
                lines.append(chunk)
                chunk = char
            else:
                chunk = candidate
        current = chunk

    if current:
        lines.append(current)
    return lines or [""]


def build_image(items, config, show_original):
    width = max(200, int(config.get("width", 500)))
    max_height = max(46, int(config.get("height", 150)))
    font_size = max(7, min(int(config.get("font_size", 10)), 20))
    opacity = max(0.0, min(float(config.get("background_opacity", 0.15)), 0.90))
    stroke = 2 if opacity <= 0.08 else 1
    wrap_width = max(80, width - 14)

    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    measure_draw = ImageDraw.Draw(dummy)
    entries = []
    y = 4
    max_right = 0

    def add_text(text, size, bold, color):
        nonlocal y, max_right
        font = _font(size, bold)
        for line in _wrap(measure_draw, text, font, wrap_width, stroke):
            line_w, line_h = _measure(measure_draw, line, font, stroke)
            entries.append((7, y, line, font, color))
            max_right = max(max_right, 7 + line_w)
            y += line_h + 1

    for item in items:
        if y >= max_height - 8:
            break
        add_text(item.nickname, max(font_size - 2, 7), True, (119, 199, 255, 255))
        add_text(item.translated, font_size, False, (255, 255, 255, 255))
        y += 2
        if show_original and item.original != item.translated:
            add_text(item.original, max(font_size - 2, 7), False, (184, 192, 200, 255))
            y += 2
        y += 3

    only_with_messages = bool(config.get("background_only_with_messages", True))

    if config.get("auto_height", True):
        if not items and not only_with_messages:
            actual_height = max_height
        else:
            actual_height = min(max_height, max(46 if items else 1, y + 2))
    else:
        actual_height = max_height

    image = Image.new("RGBA", (width, max(1, actual_height)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if config.get("compact_background", True):
        bg_width = max(70, min(width, max_right + 8))
        bg_height = max(28, min(actual_height, y + 3))
    else:
        bg_width = width
        bg_height = actual_height

    if opacity > 0.001 and (items or not only_with_messages):
        draw.rectangle(
            (0, 0, bg_width, bg_height),
            fill=(7, 17, 29, round(opacity * 255)),
        )

    for x, yy, text, font, color in entries:
        draw.text(
            (x, yy),
            text,
            font=font,
            fill=color,
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, 255),
        )

    return image, actual_height, bg_width, bg_height
