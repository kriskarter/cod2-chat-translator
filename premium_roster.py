"""Color-aware player table with three genuine, independently sized columns."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from dashboard_ui import TEXT, MUTED, AMBER, GREEN, FONT
from server_monitor import color_runs, normalized_name


class PlayerRoster(tk.Frame):
    """Keep color runs in nicknames; line up scores and ping without spaces."""

    def __init__(self, parent, *, labels, rows=4, **kwargs):
        super().__init__(parent, bg="#171613", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, minsize=68)
        self.grid_columnconfigure(2, minsize=85)
        for index, title in enumerate(labels):
            tk.Label(self, text=title, bg="#393126", fg="#E8C58A",
                     font=(FONT, 9, "bold"), anchor="w",
                     padx=9 if index == 0 else 4).grid(row=0, column=index, sticky="ew")
        tk.Label(self, bg="#393126").grid(row=0, column=3, sticky="ew")
        self.fields = []
        for column, width in enumerate((20, 7, 9)):
            widget = tk.Text(self, width=width, height=rows, wrap="none", state="disabled",
                             font=(FONT, 10), bd=0, bg="#171613", fg=TEXT,
                             padx=9 if column == 0 else 4, pady=4,
                             selectbackground="#7E562F", highlightthickness=0,
                             spacing1=2, spacing3=2, cursor="arrow")
            widget.grid(row=1, column=column, sticky="nsew")
            widget.bind("<MouseWheel>", self._wheel)
            widget.bind("<Button-4>", lambda _e: self._scroll(-1))
            widget.bind("<Button-5>", lambda _e: self._scroll(1))
            self.fields.append(widget)
        self.scroll = ttk.Scrollbar(self, orient="vertical", style="Premium.Vertical.TScrollbar",
                                    command=self._scroll_to)
        self.scroll.grid(row=1, column=3, sticky="ns")
        self.fields[0].configure(yscrollcommand=self.scroll.set)
        self.grid_rowconfigure(1, weight=1)

    def _scroll_to(self, *args):
        for field in self.fields:
            field.yview(*args)

    def _scroll(self, units):
        self._scroll_to("scroll", units, "units")
        return "break"

    def _wheel(self, event):
        return self._scroll(-1 if event.delta > 0 else 1)

    def render(self, players, *, friends=(), empty=""):
        names = {normalized_name(friend) for friend in friends}
        signature = (tuple((p.raw_name, p.score, p.ping, normalized_name(p.name) in names)
                           for p in players), empty)
        if signature == getattr(self, "_signature", None):
            return
        self._signature = signature
        position = self.fields[0].yview()[0]
        for field in self.fields:
            field.configure(state="normal")
            field.delete("1.0", "end")
        if not players:
            self.fields[0].insert("end", empty)
        for index, player in enumerate(players):
            name, score, ping = player.name, player.score, player.ping
            cell = self.fields[0]
            cell.insert("end", "★  " if normalized_name(name) in names else "     ", "friend")
            for segment, color in color_runs(player.raw_name):
                tag = "color_" + color[1:]
                cell.tag_configure(tag, foreground=color)
                cell.insert("end", segment, tag)
            cell.insert("end", "\n")
            self.fields[1].insert("end", f"{score if score is not None else '—'}\n")
            self.fields[2].insert("end", f"{ping if ping is not None else '—'} ms\n" if ping is not None else "—\n")
        self.fields[0].tag_configure("friend", foreground=AMBER)
        for field in self.fields:
            field.configure(state="disabled")
            field.yview_moveto(position)
