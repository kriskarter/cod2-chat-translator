"""Aspect preserving rendering of one integrated wartime panorama.

The soldier, city, and church share one perspective. Logo and live controls
remain independent of this artwork.
"""
from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw


@lru_cache(maxsize=1)
def _panorama():
    from app import resource_path
    with Image.open(resource_path("assets/ui_premium/command_panorama.jpg")) as art:
        return art.convert("RGB")


@lru_cache(maxsize=16)
def compose_banner(width: int, height: int) -> Image.Image:
    """Preserve the full horizontal scene, tower roof and soldier's helmet.

    The picture is 7.4:1. Wider windows crop only the lower foreground,
    keeping the church spire and helmet near the top. Cached dimensions
    avoid continuous resizing while the application is idle.
    """
    width, height = max(480, int(width)), max(120, int(height))
    art = _panorama()
    art_height = round(art.height * width / art.width)
    scaled = art.resize((width, art_height), Image.Resampling.LANCZOS)
    if art_height >= height:
        result = scaled.crop((0, 0, width, height)).convert("RGBA")
    else:
        # Narrow windows preserve both subjects without vertical distortion.
        sky = scaled.crop((0, 0, width, 1)).resize((width, height))
        ground = scaled.crop((0, art_height - 1, width, art_height))
        sky.paste(ground.resize((width, height // 2)), (0, height - height // 2))
        sky.paste(scaled, (0, (height - art_height) // 2))
        result = sky.convert("RGBA")
    shade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    alpha = Image.new("L", (width, 1))
    alpha.putdata([
        round(65 * max(0, 1 - abs(x - width * .53) / (width * .30)))
        for x in range(width)
    ])
    shade.putalpha(alpha.resize((width, height)))
    result = Image.alpha_composite(result, shade)
    draw = ImageDraw.Draw(result, "RGBA")
    draw.line((0, height - 3, width, height - 3), fill=(12, 14, 15, 230), width=2)
    draw.line((0, height - 1, width, height - 1), fill=(202, 155, 86, 205), width=1)
    return result
