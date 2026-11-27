"""Independent outgoing game HUD geometry and shared image renderer.

Coordinates are relative to the active game's monitor, in native pixels.
No native window, keyboard hook or translation worker is created for previews.
"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DEFAULTS = dict(x=24, y=440, width=720, height=200, font_size=14,
                background_opacity=.82, auto_height=True)
LIMITS = dict(x=(0, 10000), y=(0, 10000), width=(300, 1600),
              height=(145, 1200), font_size=(9, 28),
              background_opacity=(.35, .95))


def outgoing_config(raw=None):
    raw = raw if isinstance(raw, dict) else {}
    cfg = dict(DEFAULTS)
    for key, (lo, hi) in LIMITS.items():
        try:
            value = float(raw.get(key, cfg[key]))
            if math.isfinite(value):
                cfg[key] = max(lo, min(hi, value))
                if key != "background_opacity":
                    cfg[key] = int(cfg[key])
        except (ValueError, TypeError, OverflowError):
            pass
    cfg["auto_height"] = raw.get("auto_height", True) is not False
    return cfg


def positioned(raw, rect):
    cfg = outgoing_config(raw)
    left, top, width, height = map(int, rect)
    width, height = max(1, width), max(1, height)
    w, h = min(width, cfg["width"]), min(height, cfg["height"])
    x = min(cfg["x"], max(0, width - w))
    y = min(cfg["y"], max(0, height - h))
    return dict(cfg, x=left+x, y=top+y, width=w, height=h,
                max_render_height=height-y, outgoing_editor=True,
                max_messages=1, message_ttl_seconds=120,
                background_only_with_messages=True, fade_enabled=False)


def font(size, bold=False):
    return _font(int(size), bool(bold))


from functools import lru_cache


@lru_cache(maxsize=64)
def _font(size, bold):
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    for candidate in (str(windows / name), "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, face, width):
    """Measure words first; split unusually long tokens by binary search.

    Avoid measuring every prefix of every word on the GUI thread.
    """
    def measure(value):
        return draw.textlength(value, font=face)
    lines = []
    for paragraph in str(text).split("\n"):
        current = ""
        for token in re.findall(r"\s+|\S+", paragraph):
            if measure(current+token) <= width:
                current += token
                continue
            if current.strip():
                lines.append(current.rstrip())
            current = ""
            token = token.lstrip()
            while token and measure(token) > width:
                low, high = 1, len(token)
                while low < high:
                    mid = (low+high+1)//2
                    if measure(token[:mid]) <= width:
                        low = mid
                    else:
                        high = mid-1
                lines.append(token[:low])
                token = token[low:]
            current = token
        lines.append(current.rstrip())
    return lines or [""]


def render_editor(original, translated, status, cfg):
    w = max(1, int(cfg.get("width", 720)))
    h = max(1, int(cfg.get("height", 200)))
    max_h = max(h, int(cfg.get("max_render_height", h))) if cfg.get("auto_height", True) else h
    max_h = min(max_h, 1200)
    margin = min(12, max(2, w//10))
    usable = max(1, w-2*margin)
    draw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
    labels = cfg.get("editor_labels", {})
    title = labels.get("title", "F9 · Исходящий перевод") + "   " + cfg.get("route", "")
    input_label = labels.get("input", "Ввод")
    output_label = labels.get("translation", "Перевод")
    size = int(cfg.get("font_size", 14))
    def layout(px):
        main, small = font(px), font(max(9, px-2), True)
        groups = [(title, small, "#e5bd79"), (input_label+":", small, "#c1ae90"),
                  (original or "—", main, "#f7ebd5"), (output_label+":", small, "#c1ae90"),
                  (translated or "—", main, "#d3e7b5"), (status, small, "#e5bd79")]
        result = []
        for text, face, color in groups:
            lines = wrap(draw, text, face, usable)
            box = face.getbbox("Йg")
            line_h = max(px+4, box[3]-box[1]+4)
            result.append((lines,face,color,line_h))
        return result, 2*margin+sum(len(lines)*lh+3 for lines,_,_,lh in result)
    groups, needed = layout(size)
    if needed > max_h and size > 9:
        lo, hi = 9, size-1
        groups, needed = layout(lo)
        while lo <= hi:
            mid = (lo+hi)//2
            candidate, required = layout(mid)
            if required <= max_h:
                groups, needed = candidate, required
                lo = mid+1
            else:
                hi = mid-1
    height = min(max_h, max(h, needed))
    # Fixed-size windows cannot show arbitrary 500-character input at every
    # font size. Preserve the input buffer and make the visible tail explicit.
    if needed > height:
        for index in (2,4):
            lines,face,color,lh = groups[index]
            if len(lines)>1:
                groups[index] = (["…"]+lines[-1:],face,color,lh)
        while 2*margin+sum(len(g[0])*g[3]+3 for g in groups)>height:
            candidates = [i for i in (2,4,0,5) if len(groups[i][0])>1]
            if not candidates:
                break
            i = candidates[0]
            lines,face,color,lh = groups[i]
            groups[i] = ([lines[-1]],face,color,lh)
    image = Image.new("RGBA", (w,height), (17,22,25,round(float(cfg.get("background_opacity",.82))*255)))
    d = ImageDraw.Draw(image)
    d.rectangle((0,0,w-1,height-1), outline=(155,116,65,255), width=1)
    y = margin
    for lines,face,color,lh in groups:
        for line in lines:
            d.text((margin,y),line,font=face,fill=color)
            y += lh
        y += 3
    return image
