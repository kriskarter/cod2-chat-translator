"""Shared window chrome for the application's secondary Tk dialogs."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from dashboard_ui import BG, CARD, MUTED, FONT, card, check
from premium_material import SteelFrame


def dialog_body(win, title: str, subtitle: str = "", *, width: int = 580):
    """Return a live content frame below a steel title plate."""
    win.configure(bg=BG)
    win.minsize(width, 0)
    outer = SteelFrame(win, bg=BG, padx=13, pady=13)
    outer.pack(fill="both", expand=True)
    border, heading = card(outer, title, padding=8)
    border.pack(fill="x")
    if subtitle:
        tk.Label(heading, text=subtitle, bg=CARD, fg=MUTED,
                 font=(FONT, 10), anchor="w", justify="left",
                 wraplength=width-65).pack(fill="x", pady=(3, 2))
    content = ttk.Frame(outer, padding=(10, 12, 10, 5))
    content.pack(fill="both", expand=True)
    return content


def dialog_check(parent, caption, variable, callback):
    return check(parent, caption, variable, callback, surface=BG)
