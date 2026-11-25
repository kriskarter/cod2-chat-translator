"""Illustrated Home console; only the chassis is raster art.

Every switch, language selection and action remains a live Tk control bound to
the existing ControlApp variables and callbacks.  No telemetry is painted into
the artwork.  The graphic is resized at runtime; the controls follow its bays.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from dashboard_ui import BG, CARD, TEXT, MUTED, AMBER, GREEN, FONT, tr, ui_photo
from server_catalog import FEATURED_SERVER


def localized(app, ru, uk, en):
    return {"ru": ru, "uk": uk, "en": en}.get(app.ui_language, en)


class PremiumHome:
    def __init__(self, dashboard, page):
        self.dashboard = dashboard
        self.app = dashboard.app
        self.page = page
        from app import resource_path
        self.chassis_source = Image.open(resource_path(
            "assets/ui_premium/console_chassis.png")).convert("RGBA")
        self.rail_source = Image.open(resource_path(
            "assets/ui_premium/generic_panel.png")).convert("RGBA")
        self.images = {}
        self._build()

    def _build(self):
        app = self.app
        scroll = tk.Canvas(self.page, bg=BG, borderwidth=0, highlightthickness=0)
        bar = ttk.Scrollbar(self.page, orient="vertical", command=scroll.yview)
        scroll.configure(yscrollcommand=bar.set)
        scroll.pack(side="left", fill="both", expand=True)
        content = tk.Frame(scroll, bg=BG)
        window = scroll.create_window((0, 0), window=content, anchor="nw")
        self.dashboard.home_canvas = scroll
        self.dashboard.home_content = content
        self.dashboard.home_scrollbar = bar

        def scroll_size(_event=None):
            height = max(content.winfo_reqheight(), scroll.winfo_height())
            scroll.configure(scrollregion=(0, 0, scroll.winfo_width(), height))
            needed = content.winfo_reqheight() > scroll.winfo_height() + 2
            if needed and not bar.winfo_manager():
                bar.pack(side="right", fill="y")
            elif not needed and bar.winfo_manager():
                bar.pack_forget()
        content.bind("<Configure>", scroll_size)
        scroll.bind("<Configure>", lambda e: (
            scroll.itemconfigure(window, width=e.width), scroll_size()))

        self.console = tk.Canvas(content, bg=BG, borderwidth=0,
                                 highlightthickness=0, height=395)
        self.console.pack(fill="x", padx=8, pady=(5, 3))
        self.rail = tk.Canvas(content, bg=BG, borderwidth=0,
                              highlightthickness=0, height=94)
        self.rail.pack(fill="x", padx=8, pady=(0, 4))
        self.console_bg = self.console.create_image(0, 0, anchor="nw")
        self.rail_bg = self.rail.create_image(0, 0, anchor="nw")
        self._console_labels()
        self._console_widgets()
        self._rail_widgets()
        self.console.bind("<Configure>", self._layout_console)
        self.rail.bind("<Configure>", self._layout_rail)

    def _label(self, surface, x, y, value, size, *, color=TEXT, bold=False,
               anchor="w", tags=()):
        return surface.create_text(x, y, text=value, anchor=anchor, fill=color,
                                   font=(FONT, size, "bold" if bold else "normal"),
                                   tags=tags)

    def _console_labels(self):
        a = self.app
        c = self.console
        self.labels = {}
        names = {
            "heading": localized(a, "ПЕРЕВОД ЧАТА", "ПЕРЕКЛАД ЧАТУ", "CHAT TRANSLATION"),
            "incoming": localized(a, "ВХОДЯЩИЕ · F8", "ВХІДНІ · F8", "INCOMING · F8"),
            "incoming_note": localized(a, "Читаю игроков", "Читаю гравців", "Reading players"),
            "target": tr(a, "target"),
            "outgoing": localized(a, "ИСХОДЯЩИЕ · F9", "ВИХІДНІ · F9", "OUTGOING · F9"),
            "outgoing_note": localized(a, "Пишу игрокам", "Пишу гравцям", "Writing to players"),
            "my_language": tr(a, "my_language"),
            "send_language": tr(a, "send_language"),
            "preview": localized(a, "ПРЕДПРОСМОТР", "ПЕРЕГЛЯД", "PREVIEW"),
        }
        for key, value in names.items():
            self.labels[key] = self._label(c, 0, 0, value,
                20 if key == "heading" else 18 if key in {"incoming", "outgoing"}
                else 13 if key in {"incoming_note", "outgoing_note"} else 11,
                color=AMBER if key in {"target", "my_language", "send_language"}
                else MUTED if key in {"incoming_note", "outgoing_note"}
                else TEXT, bold=key in {"heading", "incoming", "outgoing", "preview"})

    def _window(self, surface, widget):
        return surface.create_window(0, 0, window=widget, anchor="nw")

    def _console_widgets(self):
        a = self.app
        c = self.console
        from app import TARGET_LANGUAGES
        from outgoing_chat import LANGUAGES
        from wwii_dashboard import tactical_switch, tactical_action
        self.controls = {}
        for key, var, callback in (
            ("f8", a.enabled_var, a.toggle_enabled),
            ("f9", a.outgoing_chat.enabled_var, a._outgoing_enabled_changed),
        ):
            self.controls[key] = self._window(c, tactical_switch(
                c, "", var, callback))
        available = list(TARGET_LANGUAGES.keys())
        custom = a._custom_language_label()
        if custom:
            available.append(custom)
        a.language_combo = ttk.Combobox(c, textvariable=a.target_name_var,
                                         values=available, state="readonly")
        a.language_combo.bind("<<ComboboxSelected>>",
                              lambda _e: a._persist_settings())
        self.controls["target"] = self._window(c, a.language_combo)
        languages = list(LANGUAGES.keys())
        for key, var in (("source", a.outgoing_chat.source_name_var),
                         ("send", a.outgoing_chat.target_name_var)):
            combo = ttk.Combobox(c, textvariable=var, values=languages,
                                 state="readonly")
            combo.bind("<<ComboboxSelected>>", a.outgoing_chat._languages_changed)
            self.controls[key] = self._window(c, combo)
        test = tactical_action(c, localized(a, "Тест", "Тест", "Test"),
                               a.test_overlay, primary=True)
        position = tactical_action(c, localized(a, "Место", "Місце", "Position"),
                                   a.toggle_overlay_edit)
        a.overlay_edit_button = position
        prefs = tactical_action(c, tr(a, "overlay"),
                                lambda: self.dashboard.navigate("overlay"))
        self.controls["test"] = self._window(c, test)
        self.controls["position"] = self._window(c, position)
        self.controls["prefs"] = self._window(c, prefs)

    def _rail_widgets(self):
        a = self.app
        r = self.rail
        from wwii_dashboard import tactical_action
        self.rail_controls = {}
        thumb = tk.Label(r, image=ui_photo(r, "premium_server.png"),
                         bg="#15130e", borderwidth=0)
        self.rail_controls["thumb"] = self._window(r, thumb)
        for key, value, size, color in (
            ("server", FEATURED_SERVER.name, 16, TEXT),
            ("address", FEATURED_SERVER.address, 11, AMBER),
            ("smart", "Smart Engine", 14, TEXT),
        ):
            self.rail_controls[key] = self._label(
                r, 0, 0, value, size, color=color, bold=True)
        # Refresh() updates these two labels using the same real runtime data.
        self.dashboard.engine_engine_bullet = tk.Label(
            r, text="●", bg="#25231D", fg=MUTED, font=(FONT, 13))
        self.dashboard.engine_engine_label = tk.Label(
            r, text="", bg="#25231D", fg=TEXT, font=(FONT, 12, "bold"))
        self.dashboard.engine_pack_label = tk.Label(
            r, text="", bg="#25231D", fg=MUTED, font=(FONT, 9))
        for key, widget in (
            ("bullet", self.dashboard.engine_engine_bullet),
            ("engine", self.dashboard.engine_engine_label),
            ("pack", self.dashboard.engine_pack_label),
        ):
            self.rail_controls[key] = self._window(r, widget)
        connect = tactical_action(r, tr(a, "connect"),
                                  a._launch_featured_server, primary=True)
        shot = tactical_action(r, tr(a, "screenshot"), a.capture_game_screenshot)
        self.rail_controls["connect"] = self._window(r, connect)
        self.rail_controls["shot"] = self._window(r, shot)

    def _photo(self, source, width, height, key):
        dimensions = (max(1, width), max(1, height))
        if key not in self.images or self.images[key][0] != dimensions:
            photo = ImageTk.PhotoImage(source.resize(dimensions,
                                                      Image.Resampling.LANCZOS),
                                       master=self.page)
            self.images[key] = (dimensions, photo)
        return self.images[key][1]

    def _layout_console(self, event):
        w = max(1, event.width)
        h = max(340, min(390, round(w * .274)))
        if self.console.cget("height") != str(h):
            self.console.configure(height=h)
        self.console.itemconfigure(self.console_bg,
                                   image=self._photo(self.chassis_source, w, h, "console"))
        c = self.console
        positions = {
            "heading": (.03, .072), "incoming": (.205, .285),
            "incoming_note": (.205, .39), "target": (.555, .255),
            "outgoing": (.205, .67), "outgoing_note": (.205, .78),
            "my_language": (.507, .635), "send_language": (.62, .635),
            "preview": (.755, .205),
        }
        for key, (x, y) in positions.items():
            c.coords(self.labels[key], round(w*x), round(h*y))
        controls = {
            "f8": (.48, .32, .055, 33), "f9": (.455, .70, .055, 33),
            "target": (.553, .32, .16, 34),
            "source": (.50, .71, .105, 34), "send": (.615, .71, .105, 34),
            "test": (.735, .75, .12, 32), "prefs": (.86, .75, .125, 32),
            "position": (.75, .865, .225, 32),
        }
        for key, (x, y, width, height) in controls.items():
            if key in ("test", "prefs"):
                native = c.nametowidget(c.itemcget(self.controls[key], "window"))
                width = max(width, (native.winfo_reqwidth()+4)/w)
                if key == "prefs":
                    x = .985-width
            c.coords(self.controls[key], round(w*x), round(h*y))
            c.itemconfigure(self.controls[key], width=max(60, round(w*width)),
                            height=height)
        # This crosshair belongs to the illustrated preview, not to a fake
        # translation status. Repaint only the lightweight canvas marks.
        c.delete("reticle")
        cx, cy = round(w*.868), round(h*.53)
        c.create_line(cx-13, cy, cx-4, cy, fill="#ff9f24", width=2,
                      tags="reticle")
        c.create_line(cx+4, cy, cx+13, cy, fill="#ff9f24", width=2,
                      tags="reticle")
        c.create_line(cx, cy-13, cx, cy-4, fill="#ff9f24", width=2,
                      tags="reticle")
        c.create_line(cx, cy+4, cx, cy+13, fill="#ff9f24", width=2,
                      tags="reticle")

    def _layout_rail(self, event):
        w, h = max(1, event.width), 94
        r = self.rail
        r.itemconfigure(self.rail_bg,
                        image=self._photo(self.rail_source, w, h, "rail"))
        # Thumbnail is source artwork only; connection state is never implied.
        r.coords(self.rail_controls["thumb"], 11, 6)
        r.itemconfigure(self.rail_controls["thumb"], width=180, height=80)
        for key, x, y in (
            ("server", .16, .31), ("address", .16, .66),
            ("smart", .58, .32),
        ):
            r.coords(self.rail_controls[key], round(w*x), round(h*y))
        for key, x, y, width, height in (
            ("connect", .39, .27, .17, 41),
            ("bullet", .58, .55, .02, 25),
            ("engine", .61, .54, .17, 25),
            ("pack", .59, .78, .21, 20),
            ("shot", .82, .27, .16, 41),
        ):
            r.coords(self.rail_controls[key], round(w*x), round(h*y))
            r.itemconfigure(self.rail_controls[key], width=max(24, round(w*width)),
                            height=height)


def build_premium_home(dashboard, page):
    dashboard.premium_home = PremiumHome(dashboard, page)
