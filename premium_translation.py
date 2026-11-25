"""Translation expert console: passive WWII art and live independent F8/F9 controls."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from dashboard_ui import BG, TEXT, MUTED, AMBER, FONT, tr, check
from premium_home import localized


class TranslationConsole:
    def __init__(self, dashboard, page):
        self.dashboard = dashboard
        self.app = dashboard.app
        from app import resource_path
        self.art = Image.open(resource_path(
            "assets/ui_premium/translation_chassis.png")).convert("RGBA")
        self.content = dashboard._scroll_page(page, tr(self.app, "translation_head"),
                                               tr(self.app, "actual"))
        self.canvas = tk.Canvas(self.content, bg=BG, highlightthickness=0,
                                borderwidth=0, height=390)
        self.canvas.pack(fill="x", padx=13, pady=(0, 9))
        self.back = self.canvas.create_image(0, 0, anchor="nw")
        self.photo = None
        self.widgets = {}
        self.labels = {}
        self._build()
        self.canvas.bind("<Configure>", self._layout)

    def label(self, key, value, size, color=TEXT, bold=False):
        self.labels[key] = self.canvas.create_text(
            0, 0, text=value, anchor="w", fill=color,
            font=(FONT, size, "bold" if bold else "normal"))

    def widget(self, key, widget):
        self.widgets[key] = self.canvas.create_window(
            0, 0, window=widget, anchor="nw")

    def _build(self):
        app = self.app
        c = self.canvas
        from wwii_dashboard import tactical_switch
        from app import TARGET_LANGUAGES
        from outgoing_chat import LANGUAGES
        self.label("heading", tr(app, "translation_head").upper(), 20, TEXT, True)
        self.label("incoming", localized(app, "ВХОДЯЩИЙ ЧАТ · F8", "ВХІДНИЙ ЧАТ · F8",
                                          "INCOMING CHAT · F8"), 19, TEXT, True)
        self.label("outgoing", localized(app, "ИСХОДЯЩИЙ ЧАТ · F9", "ВИХІДНИЙ ЧАТ · F9",
                                          "OUTGOING CHAT · F9"), 19, TEXT, True)
        self.label("f8_note", tr(app, "f8_note"), 11, MUTED)
        self.label("f9_note", tr(app, "f9_note"), 11, MUTED)
        for key, title in (("target", "target"), ("style", "style"),
                           ("source", "my_language"), ("send", "send_language")):
            self.label(key, tr(app, title), 11, AMBER, True)
        self.widget("f8", tactical_switch(c, "", app.enabled_var, app.toggle_enabled))
        self.widget("f9", tactical_switch(c, "", app.outgoing_chat.enabled_var,
                                          app._outgoing_enabled_changed))
        custom = app._custom_language_label()
        targets = list(TARGET_LANGUAGES.keys()) + ([custom] if custom else [])
        app.language_combo = ttk.Combobox(c, values=targets,
                                          textvariable=app.target_name_var,
                                          state="readonly")
        app.language_combo.bind("<<ComboboxSelected>>",
                                lambda _e: app._persist_settings())
        self.widget("target_combo", app.language_combo)
        styles = [app._style_label(code) for code in ("clear", "live", "raw")]
        app.slang_style_var.set(app._style_label(str(app.config.get("slang_style", "live"))))
        style = ttk.Combobox(c, values=styles, textvariable=app.slang_style_var,
                             state="readonly")
        style.bind("<<ComboboxSelected>>", lambda _e: app._persist_settings())
        self.widget("style_combo", style)
        for key, var, cb in (
            ("smart_enabled", app.smart_engine_var, app._persist_settings),
            ("slang", app.slang_var, app._persist_settings),
            ("dedupe", app.dedupe_var, app._persist_settings),
            ("original", app.show_original_var, app.toggle_original),
            ("hide_same", app.hide_same_var, app._persist_settings),
        ):
            self.widget(key, check(c, tr(app, key), var, cb))
        languages = list(LANGUAGES.keys())
        for key, var in (("source_combo", app.outgoing_chat.source_name_var),
                         ("send_combo", app.outgoing_chat.target_name_var)):
            combo = ttk.Combobox(c, values=languages, textvariable=var,
                                 state="readonly")
            combo.bind("<<ComboboxSelected>>", app.outgoing_chat._languages_changed)
            self.widget(key, combo)
        route = tk.Label(c, textvariable=app.outgoing_chat.route_var,
                         bg="#1B1B15", fg=AMBER, font=(FONT, 14, "bold"),
                         anchor="w")
        self.widget("route", route)

    def _layout(self, event):
        w = max(1, event.width)
        h = max(360, min(420, round(w * .30)))
        if self.canvas.cget("height") != str(h):
            self.canvas.configure(height=h)
        self.photo = ImageTk.PhotoImage(
            self.art.resize((w, h), Image.Resampling.LANCZOS),
            master=self.canvas)
        c = self.canvas
        c.itemconfigure(self.back, image=self.photo)
        labels = {
            "heading": (.035, .07), "incoming": (.19, .285),
            "outgoing": (.19, .69), "f8_note": (.19, .375),
            "f9_note": (.19, .78), "target": (.585, .265),
            "style": (.77, .265), "source": (.585, .65),
            "send": (.77, .65),
        }
        for key, (x, y) in labels.items():
            c.coords(self.labels[key], round(w*x), round(h*y))
        geometry = {
            "f8": (.48, .325, .055, 30), "f9": (.48, .73, .055, 30),
            "target_combo": (.585, .32, .165, 32),
            "style_combo": (.77, .32, .16, 32),
            "smart_enabled": (.19, .405, .16, 26),
            "slang": (.36, .405, .16, 26),
            "dedupe": (.53, .405, .16, 26),
            "original": (.70, .405, .20, 26),
            "hide_same": (.19, .465, .28, 26),
            "source_combo": (.585, .71, .165, 32),
            "send_combo": (.77, .71, .16, 32),
            "route": (.585, .835, .35, 28),
        }
        for key, (x, y, width, height) in geometry.items():
            item = self.widgets[key]
            c.coords(item, round(w*x), round(h*y))
            c.itemconfigure(item, width=max(50, round(w*width)), height=height)


def translation_canvas_page(dashboard, page):
    dashboard.premium_translation = TranslationConsole(dashboard, page)
