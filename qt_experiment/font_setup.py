"""Use installed Windows fonts in Qt offscreen evidence; never bundle OS fonts."""
from __future__ import annotations
import os
from pathlib import Path

def prepare_font_environment():
    if os.name=="nt" and os.environ.get("QT_QPA_PLATFORM","").split(":")[0]=="offscreen":
        # The offscreen Windows platform uses a FreeType font database instead
        # of the normal Windows system font enumeration.
        directory=Path(os.environ.get("SystemRoot",r"C:\Windows"))/"Fonts"
        if directory.is_dir(): os.environ.setdefault("QT_QPA_FONTDIR",str(directory))

def font_has_ui_glyphs(font):
    from PySide6.QtGui import QRawFont
    raw=QRawFont.fromFont(font)
    return raw.isValid() and all(raw.supportsCharacter(ord(ch)) for ch in "F89 AaЖжЇїЄєІіҐґЯя0123456789")

def ensure_ui_font(app):
    from PySide6.QtGui import QFont,QFontDatabase
    if app is None: return False
    if app.property("_cod2_font_ready"): return True
    if os.name=="nt":
        # The native Windows backend already discovers system fonts. Only
        # register the installed faces explicitly when offscreen cannot see them.
        candidates=("Segoe UI","Arial")
        def suitable(name):
            font=QFont(name)
            if not font_has_ui_glyphs(font): return False
            font.setBold(True)
            return font_has_ui_glyphs(font)
        family=next((name for name in candidates if name in QFontDatabase.families() and suitable(name)),None)
        if family is None:
            directory=Path(os.environ.get("SystemRoot",r"C:\Windows"))/"Fonts"
            for file in ("segoeui.ttf","segoeuib.ttf","arial.ttf","arialbd.ttf"):
                path=directory/file
                if path.is_file(): QFontDatabase.addApplicationFont(str(path))
            family=next((name for name in candidates if suitable(name)),None)
        if family is not None:
            font=app.font();font.setFamily(family);app.setFont(font)
    elif not font_has_ui_glyphs(app.font()):
        # Minimal Linux/offscreen images may expose a generic family whose
        # first resolved face lacks Cyrillic despite installed Unicode fonts.
        for family in ("DejaVu Sans", "Noto Sans", "Liberation Sans"):
            candidate=QFont(family)
            if font_has_ui_glyphs(candidate):
                app.setFont(candidate)
                break
    font=app.font()
    valid=font_has_ui_glyphs(font)
    font.setBold(True)
    valid=valid and font_has_ui_glyphs(font)
    if valid: app.setProperty("_cod2_font_ready",True)
    return valid
