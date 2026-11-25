"""Resizeable illustrated metal surfaces.  Only decoration is rasterized.

The controls, captions and values over these canvases remain real Tk widgets.
Recompositing is debounced and limited to the sizes actually used by the UI.
"""
from __future__ import annotations

import tkinter as tk
from functools import lru_cache
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageOps


@lru_cache(maxsize=32)
def panel_image(width: int, height: int, scene: str = "") -> Image.Image:
    from app import resource_path
    width, height = max(80, width), max(60, height)
    source = Image.open(resource_path("assets/ui_premium/generic_panel.png")).convert("RGBA")
    result = Image.new("RGBA", (width, height), (19, 17, 14, 255))
    inset = 17
    if scene:
        artwork = Image.open(resource_path(scene)).convert("RGB")
        if "monitor_hero" in scene:
            artwork = ImageOps.mirror(artwork)
        target_width, target_height = width - 2 * inset, height - 2 * inset
        scale = max(target_width / artwork.width, target_height / artwork.height)
        artwork = artwork.resize((round(artwork.width * scale), round(artwork.height * scale)), Image.Resampling.LANCZOS)
        # The illustrated cards reserve their left half for controls. Keep
        # the right-hand scene in view when the card is much wider than tall.
        left = max(0, artwork.width - target_width) if "translation_card" in scene else (artwork.width - target_width) // 2
        top = (artwork.height - target_height) // 2
        result.paste(artwork.crop((left, top, left + target_width, top + target_height)), (inset, inset))
        # The text is drawn on the same RGBA surface as the artwork. A soft
        # local shadow preserves contrast without an opaque widget rectangle.
        shade = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
        alpha = Image.new("L", (target_width, 1))
        alpha.putdata([int(110 * max(0, 1 - x / max(1, target_width * .82)))
                       for x in range(target_width)])
        shade.putalpha(alpha.resize((target_width, target_height)))
        result.alpha_composite(shade, (inset, inset))
    else:
        steel = Image.open(resource_path("assets/ui_premium/steel_source.png")).convert("RGB")
        steel = ImageEnhance.Brightness(steel).enhance(.55)
        result.paste(steel.resize((width - 2 * inset, height - 2 * inset)), (inset, inset))

    # Sample each corner and edge independently.  Never stretch the rivets.
    src_margin = 86
    dst_margin = min(22, width // 5, height // 5)
    sx = (0, src_margin, source.width - src_margin, source.width)
    sy = (0, src_margin, source.height - src_margin, source.height)
    dx = (0, dst_margin, width - dst_margin, width)
    dy = (0, dst_margin, height - dst_margin, height)
    for row in range(3):
        for col in range(3):
            if row == col == 1:
                continue
            tile = source.crop((sx[col], sy[row], sx[col + 1], sy[row + 1]))
            tile = tile.resize((dx[col + 1] - dx[col], dy[row + 1] - dy[row]), Image.Resampling.LANCZOS)
            result.alpha_composite(tile, (dx[col], dy[row]))
    return result


class MetalCanvas(tk.Canvas):
    """Canvas with a responsive nine-slice illustration underneath live widgets."""

    def __init__(self, parent, *, scene="", **kwargs):
        super().__init__(parent, bg="#17150F", highlightthickness=0, bd=0, **kwargs)
        self._scene = scene
        self._photo = None
        self._size = None
        self._pending = None
        self._background = self.create_image(0, 0, anchor="nw")
        self.bind("<Configure>", self._resized)

    def _resized(self, event):
        size = (max(80, event.width), max(60, event.height))
        if size == self._size:
            return
        self._size = size
        if self._pending is not None:
            self.after_cancel(self._pending)
        self._pending = self.after(45, self._redraw)

    def _redraw(self):
        self._pending = None
        self._photo = ImageTk.PhotoImage(panel_image(*self._size, self._scene), master=self)
        self.itemconfigure(self._background, image=self._photo)
        self.tag_lower(self._background)


class Keycap(tk.Canvas):
    """Keyboard accessible metallic key; live title and real switch callback."""

    def __init__(self, parent, caption: str, command, *, size=104):
        super().__init__(parent, width=size, height=size, bg="#211D17", bd=0,
                         highlightthickness=0, cursor="hand2", takefocus=1)
        from app import resource_path
        source = Image.open(resource_path("assets/ui_wwii/premium_keycap.png")).convert("RGBA")
        source = source.resize((size, size), Image.Resampling.LANCZOS)
        self._states = {}
        for state, brightness in (("normal", 1), ("hover", 1.17), ("pressed", .77)):
            self._states[state] = ImageTk.PhotoImage(ImageEnhance.Brightness(source).enhance(brightness), master=self)
        self._face = self.create_image(0, 0, image=self._states["normal"], anchor="nw")
        self.create_text(size // 2, size // 2 + 2, text=caption, fill="#FFE0A2",
                         font=("Bahnschrift SemiCondensed", 26, "bold"))
        self.command = command
        self.bind("<Enter>", lambda _e: self._set("hover"))
        self.bind("<Leave>", lambda _e: self._set("normal"))
        self.bind("<ButtonPress-1>", lambda _e: self._set("pressed"))
        self.bind("<ButtonRelease-1>", lambda e: (self._set("hover"), self.command()) if 0 <= e.x < size and 0 <= e.y < size else self._set("normal"))
        self.bind("<Return>", lambda _e: self.command())
        self.bind("<space>", lambda _e: self.command())
        self.bind("<FocusIn>", lambda _e: self.configure(highlightthickness=2, highlightcolor="#F8BB65"))
        self.bind("<FocusOut>", lambda _e: self.configure(highlightthickness=0))

    def _set(self, state):
        self.itemconfigure(self._face, image=self._states[state])

    def invoke(self):
        """Match Tk button activation for keyboard, tests and assistive tools."""
        return self.command()


class CanvasKeycap:
    """A focusable canvas control that shares its card's illustrated surface."""

    def __init__(self, canvas, caption, command, *, size=104, x=22):
        from app import resource_path
        self.canvas, self.command, self.size = canvas, command, size
        source = Image.open(resource_path("assets/ui_wwii/premium_keycap.png")).convert("RGBA")
        source = source.resize((size, size), Image.Resampling.LANCZOS)
        self.photos = {state: ImageTk.PhotoImage(ImageEnhance.Brightness(source).enhance(brightness), master=canvas)
                       for state, brightness in (("normal", 1), ("hover", 1.16), ("pressed", .76), ("disabled", .62))}
        self.face = canvas.create_image(x, 0, image=self.photos["normal"], anchor="w", tags=("keycap",))
        self.caption = canvas.create_text(x + size // 2, 0, text=caption,
            fill="#FFE0A2", font=("Bahnschrift SemiCondensed", 26, "bold"), tags=("keycap",))
        canvas.configure(takefocus=1, cursor="hand2")
        canvas.tag_bind("keycap", "<Enter>", lambda _e: self._set("hover"))
        canvas.tag_bind("keycap", "<Leave>", lambda _e: self._set("normal"))
        canvas.tag_bind("keycap", "<ButtonPress-1>", self._press)
        canvas.tag_bind("keycap", "<ButtonRelease-1>", self._release)
        canvas.bind("<Return>", lambda _e: self.invoke())
        canvas.bind("<space>", lambda _e: self.invoke())
        canvas.bind("<FocusIn>", lambda _e: canvas.itemconfigure(self.caption, fill="#FFF4D3"))
        canvas.bind("<FocusOut>", lambda _e: canvas.itemconfigure(self.caption, fill="#FFE0A2"))
        canvas.bind("<Configure>", self._center, add="+")

    def _center(self, event):
        self.canvas.coords(self.face, 22, event.height // 2)
        self.canvas.coords(self.caption, 22 + self.size // 2, event.height // 2 + 2)

    def _set(self, state):
        self.canvas.itemconfigure(self.face, image=self.photos[state])

    def _press(self, _event):
        self.canvas.focus_set()
        self._set("pressed")

    def _release(self, event):
        self._set("hover")
        if self.canvas.find_withtag("current") and "keycap" in self.canvas.gettags("current"):
            self.invoke()

    def invoke(self):
        return self.command()
