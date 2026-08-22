from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

from PIL import Image, ImageChops, ImageDraw, ImageFont


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_ubyte),
        ("BlendFlags", ctypes.c_ubyte),
        ("SourceConstantAlpha", ctypes.c_ubyte),
        ("AlphaFormat", ctypes.c_ubyte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HANDLE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HANDLE),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HANDLE

user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.DefWindowProcW.restype = LRESULT

user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype = wintypes.WORD

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HANDLE,
    wintypes.HANDLE,
    ctypes.c_void_p,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC

user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND,
    wintypes.HDC,
    ctypes.POINTER(POINT),
    ctypes.POINTER(SIZE),
    wintypes.HDC,
    ctypes.POINTER(POINT),
    wintypes.DWORD,
    ctypes.POINTER(BLENDFUNCTION),
    wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC

gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL

gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC,
    ctypes.POINTER(BITMAPINFO),
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.HANDLE,
    wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = wintypes.HANDLE

gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi32.SelectObject.restype = wintypes.HANDLE

gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL



def _wndproc(hwnd, msg, wparam, lparam):
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


WNDPROC_CALLBACK = WNDPROC(_wndproc)
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


def _premultiplied_bgra(image):
    red, green, blue, alpha = image.convert("RGBA").split()
    red = ImageChops.multiply(red, alpha)
    green = ImageChops.multiply(green, alpha)
    blue = ImageChops.multiply(blue, alpha)
    return Image.merge("RGBA", (red, green, blue, alpha)).tobytes("raw", "BGRA")


class Win32LayeredOverlay:
    CLASS_NAME = "CoD2ChatTranslatorNativeOverlayV1"

    WS_POPUP = 0x80000000
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_LAYERED = 0x00080000
    WS_EX_NOACTIVATE = 0x08000000

    SW_HIDE = 0
    SW_SHOWNOACTIVATE = 4
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010

    ULW_ALPHA = 0x00000002
    AC_SRC_OVER = 0x00
    AC_SRC_ALPHA = 0x01
    DIB_RGB_COLORS = 0
    BI_RGB = 0

    def __init__(self):
        self.hinstance = kernel32.GetModuleHandleW(None)
        self._register_class()

        ex_style = (
            self.WS_EX_LAYERED
            | self.WS_EX_TRANSPARENT
            | self.WS_EX_TOOLWINDOW
            | self.WS_EX_TOPMOST
            | self.WS_EX_NOACTIVATE
        )
        self.hwnd = user32.CreateWindowExW(
            ex_style,
            self.CLASS_NAME,
            "",
            self.WS_POPUP,
            0,
            0,
            1,
            1,
            None,
            None,
            self.hinstance,
            None,
        )
        if not self.hwnd:
            raise ctypes.WinError(ctypes.get_last_error())

        self.image = None
        self.x = 0
        self.y = 0
        self.alpha = 1.0

    def _register_class(self):
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = WNDPROC_CALLBACK
        wc.hInstance = self.hinstance
        wc.lpszClassName = self.CLASS_NAME

        atom = user32.RegisterClassExW(ctypes.byref(wc))
        if atom:
            return

        error = ctypes.get_last_error()
        if error != 1410:
            raise ctypes.WinError(error)

    def render(self, items, config, show_original, alpha=1.0):
        self.image, actual_height, bg_width, bg_height = build_image(
            items,
            config,
            show_original,
        )
        self.x = int(config.get("x", 8))
        self.y = int(config.get("y", 360))
        self.alpha = max(0.0, min(float(alpha), 1.0))
        self._present()
        return actual_height, bg_width, bg_height

    def _present(self):
        if not self.hwnd or self.image is None:
            return

        width, height = self.image.size
        raw = _premultiplied_bgra(self.image)

        screen_dc = user32.GetDC(None)
        if not screen_dc:
            raise ctypes.WinError(ctypes.get_last_error())

        memory_dc = None
        bitmap = None
        old_object = None

        try:
            memory_dc = gdi32.CreateCompatibleDC(screen_dc)
            if not memory_dc:
                raise ctypes.WinError(ctypes.get_last_error())

            info = BITMAPINFO()
            info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            info.bmiHeader.biWidth = width
            info.bmiHeader.biHeight = -height
            info.bmiHeader.biPlanes = 1
            info.bmiHeader.biBitCount = 32
            info.bmiHeader.biCompression = self.BI_RGB

            bits = ctypes.c_void_p()
            bitmap = gdi32.CreateDIBSection(
                screen_dc,
                ctypes.byref(info),
                self.DIB_RGB_COLORS,
                ctypes.byref(bits),
                None,
                0,
            )
            if not bitmap or not bits.value:
                raise ctypes.WinError(ctypes.get_last_error())

            ctypes.memmove(bits.value, raw, len(raw))
            old_object = gdi32.SelectObject(memory_dc, bitmap)

            dst = POINT(self.x, self.y)
            size = SIZE(width, height)
            src = POINT(0, 0)
            blend = BLENDFUNCTION(
                self.AC_SRC_OVER,
                0,
                round(self.alpha * 255),
                self.AC_SRC_ALPHA,
            )

            if not user32.UpdateLayeredWindow(
                self.hwnd,
                screen_dc,
                ctypes.byref(dst),
                ctypes.byref(size),
                memory_dc,
                ctypes.byref(src),
                0,
                ctypes.byref(blend),
                self.ULW_ALPHA,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            if memory_dc and old_object:
                gdi32.SelectObject(memory_dc, old_object)
            if bitmap:
                gdi32.DeleteObject(bitmap)
            if memory_dc:
                gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(None, screen_dc)

    def set_alpha(self, alpha):
        self.alpha = max(0.0, min(float(alpha), 1.0))
        if self.image is not None:
            self._present()

    def move(self, x, y):
        self.x = int(x)
        self.y = int(y)
        if self.hwnd:
            user32.SetWindowPos(
                self.hwnd,
                wintypes.HWND(-1),
                self.x,
                self.y,
                0,
                0,
                self.SWP_NOSIZE | self.SWP_NOACTIVATE,
            )

    def force_topmost(self):
        if self.hwnd:
            user32.SetWindowPos(
                self.hwnd,
                wintypes.HWND(-1),
                0,
                0,
                0,
                0,
                self.SWP_NOSIZE | self.SWP_NOMOVE | self.SWP_NOACTIVATE,
            )

    def show(self):
        if self.hwnd:
            user32.ShowWindow(self.hwnd, self.SW_SHOWNOACTIVATE)
            self.force_topmost()

    def hide(self):
        if self.hwnd:
            user32.ShowWindow(self.hwnd, self.SW_HIDE)

    def destroy(self):
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None


def install_native_overlay(overlay_cls):
    """Use a native per-pixel-alpha HWND during normal Windows gameplay.

    The existing Tk overlay remains intact for edit mode and as a fallback.
    """

    original_init = overlay_cls.__init__
    original_apply_geometry = overlay_cls._apply_geometry
    original_force_topmost_native = overlay_cls._force_topmost_native
    original_apply_background_visibility = overlay_cls._apply_background_visibility
    original_set_text_alpha = overlay_cls._set_text_alpha
    original_set_visible = overlay_cls.set_visible
    original_set_edit_mode = overlay_cls.set_edit_mode
    original_render = overlay_cls.render
    original_fade_out_and_clear = overlay_cls._fade_out_and_clear

    def native_play_mode(self):
        return (
            getattr(self, "_native_surface", None) is not None
            and not getattr(self, "edit_mode", False)
        )

    def patched_init(self, *args, **kwargs):
        self._native_surface = None
        self._native_visible = True
        original_init(self, *args, **kwargs)

        try:
            self._native_surface = Win32LayeredOverlay()
            self.window.withdraw()
            self.bg_window.withdraw()
            self.render()
        except Exception:
            try:
                if self._native_surface is not None:
                    self._native_surface.destroy()
            except Exception:
                pass
            self._native_surface = None
            try:
                self.window.deiconify()
                original_apply_background_visibility(self)
                original_render(self)
            except Exception:
                pass

    def patched_apply_geometry(self, force_config_height=False):
        if native_play_mode(self):
            try:
                x, y, _width, _height = self._geometry_values(
                    force_config_height=force_config_height
                )
                self._native_surface.move(x, y)
                return
            except Exception:
                pass
        return original_apply_geometry(
            self,
            force_config_height=force_config_height,
        )

    def patched_force_topmost_native(self):
        if native_play_mode(self):
            try:
                self._native_surface.force_topmost()
                return
            except Exception:
                pass
        return original_force_topmost_native(self)

    def patched_keep_topmost(self):
        try:
            if native_play_mode(self):
                if getattr(self, "_native_visible", True):
                    self._native_surface.force_topmost()
            elif (
                self.window.winfo_exists()
                and self.window.state() != "withdrawn"
            ):
                self._force_topmost_native()
        except Exception:
            pass

        try:
            self.root.after(1000, self._keep_topmost)
        except Exception:
            pass

    def patched_apply_background_visibility(self):
        if native_play_mode(self):
            try:
                self.window.withdraw()
                self.bg_window.withdraw()
            except Exception:
                pass
            return
        return original_apply_background_visibility(self)

    def patched_set_text_alpha(self, alpha):
        if not native_play_mode(self):
            return original_set_text_alpha(self, alpha)

        target = max(0.0, min(float(alpha), 1.0))
        changed = abs(target - float(getattr(self, "_fade_alpha", 1.0))) > 0.001
        self._fade_alpha = target

        if changed:
            try:
                self._native_surface.set_alpha(target)
            except Exception:
                pass

    def patched_set_visible(self, visible):
        self._native_visible = bool(visible)

        if native_play_mode(self):
            try:
                self.window.withdraw()
                self.bg_window.withdraw()

                if self._native_visible:
                    self.render()
                    self._native_surface.show()
                else:
                    self._native_surface.hide()
                return
            except Exception:
                pass

        return original_set_visible(self, visible)

    def patched_set_edit_mode(self, enabled):
        enabled = bool(enabled)

        if getattr(self, "_native_surface", None) is None:
            return original_set_edit_mode(self, enabled)

        if enabled:
            try:
                self._native_surface.hide()
            except Exception:
                pass

            self.edit_mode = True
            try:
                self.window.deiconify()
            except Exception:
                pass

            return original_set_edit_mode(self, True)

        self._cancel_fade()
        self.edit_mode = False
        self._fade_alpha = 1.0

        try:
            self.window.withdraw()
            self.bg_window.withdraw()
        except Exception:
            pass

        self.render()

    def patched_render(self):
        if not native_play_mode(self):
            return original_render(self)

        try:
            self.window.withdraw()
            self.bg_window.withdraw()

            (
                self._actual_height,
                self._background_width,
                self._background_height,
            ) = self._native_surface.render(
                list(self.items),
                self._overlay_cfg(),
                bool(self.config.get("show_original", False)),
                self._fade_alpha,
            )

            if getattr(self, "_native_visible", True):
                self._native_surface.show()
            else:
                self._native_surface.hide()

            return
        except Exception:
            try:
                self._native_surface.destroy()
            except Exception:
                pass

            self._native_surface = None

            try:
                self.window.deiconify()
            except Exception:
                pass

            return original_render(self)

    def patched_fade_out_and_clear(self):
        if not native_play_mode(self):
            return original_fade_out_and_clear(self)

        if not self.items:
            return

        ms = int(self._overlay_cfg().get("fade_ms", 220))
        start = self._fade_alpha

        def done():
            self.items.clear()
            # Keep alpha at zero until the empty frame has replaced the old one.
            self.render()
            self._set_text_alpha(1.0)

        self._animate_alpha(
            start,
            0.0,
            max(100, ms),
            on_done=done,
        )

    overlay_cls._native_play_mode = native_play_mode
    overlay_cls.__init__ = patched_init
    overlay_cls._apply_geometry = patched_apply_geometry
    overlay_cls._force_topmost_native = patched_force_topmost_native
    overlay_cls._keep_topmost = patched_keep_topmost
    overlay_cls._apply_background_visibility = patched_apply_background_visibility
    overlay_cls._set_text_alpha = patched_set_text_alpha
    overlay_cls.set_visible = patched_set_visible
    overlay_cls.set_edit_mode = patched_set_edit_mode
    overlay_cls.render = patched_render
    overlay_cls._fade_out_and_clear = patched_fade_out_and_clear
