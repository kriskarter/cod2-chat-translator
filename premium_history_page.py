"""Recent in-memory application events; never expose raw console_mp.log."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dashboard_ui import BG,CARD,TEXT,MUTED,AMBER,FONT
from premium_home import local,txt


def build_history_page(dashboard,page):
    app=dashboard.app
    box=tk.Frame(page,bg=BG)
    box.pack(fill="both",expand=True,padx=20,pady=15)
    txt(box,local(app,"ЛОГИ И ИСТОРИЯ","ЖУРНАЛИ ТА ІСТОРІЯ","LOGS AND HISTORY"),
        19,AMBER,True,bg=BG).pack(anchor="w")
    txt(box,local(app,"Последние события этой сессии. Игровой журнал и пароли сервера здесь не показываются.",
                  "Останні події цієї сесії. Ігровий журнал і паролі сервера тут не показуються.",
                  "Recent events from this session. Raw game logs and server passwords are not displayed."),
        10,MUTED,bg=BG).pack(anchor="w",pady=(2,12))
    frame=tk.Frame(box,bg="#9B7545",padx=2,pady=2)
    frame.pack(fill="both",expand=True)
    history=tk.Text(frame,bg=CARD,fg=TEXT,bd=0,highlightthickness=0,
                    state="disabled",font=(FONT,11),wrap="word",padx=14,pady=10)
    history.pack(side="left",fill="both",expand=True)
    bar=ttk.Scrollbar(frame,orient="vertical",style="Premium.Vertical.TScrollbar",command=history.yview)
    bar.pack(side="right",fill="y")
    history.configure(yscrollcommand=bar.set)
    dashboard.history_text=history


def record(dashboard,message):
    widget=getattr(dashboard,"history_text",None)
    if widget is None or not widget.winfo_exists():return
    from datetime import datetime
    from time import monotonic
    stamp=monotonic()
    previous=getattr(dashboard,"_history_last",None)
    if previous and previous[0]==str(message) and stamp-previous[1]<30:
        return
    dashboard._history_last=(str(message),stamp)
    widget.configure(state="normal")
    widget.insert("end",datetime.now().strftime("%H:%M:%S")+"   "+str(message)[:240]+"\n")
    if int(widget.index("end-1c").split(".")[0])>250:
        widget.delete("1.0","3.0")
    widget.see("end")
    widget.configure(state="disabled")
