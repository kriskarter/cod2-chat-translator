"""Expert pages built from the same illustrated metal components as Home.

The graphics are passive material. Tk controls retain existing variables,
callbacks and keyboard behavior; player data and the game overlay are not
simulated by this module.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from dashboard_ui import CARD, TEXT, MUTED, AMBER, FONT, tr, text, card, action, check, label_combo


def _row(parent):
    row=tk.Frame(parent,bg=CARD)
    row.pack(fill="x",pady=(8,0))
    return row


def overlay_page(dashboard,page):
    app=dashboard.app
    content=dashboard._scroll_page(page,tr(app,"overlay_head"),tr(app,"overlay_hint"))
    columns=tk.Frame(content,bg=content.cget("bg"))
    columns.pack(fill="both",expand=True,padx=14,pady=(0,9))
    columns.columnconfigure(0,weight=1,uniform="overlay")
    columns.columnconfigure(1,weight=1,uniform="overlay")
    left_border,left=card(columns,tr(app,"overlay_view"))
    right_border,right=card(columns,
        {"ru":"ПРЕДПРОСМОТР · ОБРАЗЕЦ", "uk":"ПЕРЕГЛЯД · ЗРАЗОК",
         "en":"PREVIEW · SAMPLE"}.get(app.ui_language,"PREVIEW · SAMPLE"))
    left_border.grid(row=0,column=0,sticky="nsew",padx=(0,5))
    right_border.grid(row=0,column=1,sticky="nsew",padx=(5,0))

    # F8 controls the incoming overlay. No third, fictional enable state.
    check(left,tr(app,"app_active"),app.enabled_var,app.toggle_enabled).pack(anchor="w")
    tk.Label(left,textvariable=app.overlay_hotkey_status_var,bg=CARD,
             fg=AMBER,font=(FONT,9,"bold"),anchor="w").pack(anchor="w",pady=(4,9))
    for title,value_var,label_var,start,end,fn in (
        ("font_size",app.font_var,app.font_label_var,7,20,app._font_slider),
        ("opacity",app.bg_var,app.bg_label_var,0,90,app._background_slider),
        ("time",app.ttl_var,app.ttl_label_var,5,20,app._ttl_slider),
    ):
        row=tk.Frame(left,bg=CARD)
        row.pack(fill="x",pady=4)
        text(row,tr(app,title),color=MUTED,size=10).pack(side="left")
        tk.Label(row,textvariable=label_var,fg=AMBER,bg=CARD,
                 font=(FONT,10,"bold"),width=6).pack(side="right")
        scale=ttk.Scale(row,from_=start,to=end,orient="horizontal",command=fn)
        scale.set(value_var.get())
        scale.pack(side="right",fill="x",expand=True,padx=(12,8))
    counts=_row(left)
    text(counts,tr(app,"messages"),color=MUTED,size=10).pack(side="left")
    from app import MIN_OVERLAY_MESSAGES,MAX_OVERLAY_MESSAGES
    amount=ttk.Combobox(counts,state="readonly",
        values=list(range(MIN_OVERLAY_MESSAGES,MAX_OVERLAY_MESSAGES+1)),
        textvariable=app.max_messages_var,width=5)
    amount.pack(side="left",padx=10)
    amount.bind("<<ComboboxSelected>>",lambda _e:app._max_messages_changed())
    for title,var,fn in (
        ("bg_only",app.bg_only_var,app._background_only_changed),
        ("compact_bg",app.compact_bg_var,app._compact_background_changed),
        ("fade",app.fade_var,app._fade_changed),
    ):
        check(left,tr(app,title),var,fn).pack(anchor="w",pady=1)
    presets=_row(left)
    for title,fn in (("text_only",app.text_only_preset),
                     ("minimal",app.minimal_preset),
                     ("readable",app.readable_preset)):
        action(presets,tr(app,title),fn).pack(side="left",padx=(0,6))

    # The image is a demonstration of presentation only, never a claim that
    # an in-game message was observed in this isolated interface.
    from PIL import Image,ImageTk
    from app import resource_path
    scene=Image.open(resource_path("assets/ui_premium/hero_source.png")).convert("RGB")
    scene=scene.resize((520,175),Image.Resampling.LANCZOS)
    photo=ImageTk.PhotoImage(scene,master=right)
    preview=tk.Canvas(right,width=520,height=235,highlightthickness=1,
                       highlightbackground="#B68A4E",bg="#11120e")
    preview.pack(fill="x",pady=(3,10))
    preview.image=photo
    preview.create_image(0,0,anchor="nw",image=photo)
    preview.create_rectangle(8,150,514,225,fill="#14160e",outline="#8B6A3D")
    sample={"ru":("Игрок: Hold the left flank!","Образец: Держите левый фланг!"),
            "uk":("Гравець: Hold the left flank!","Зразок: Тримайте лівий фланг!"),
            "en":("Player: Hold the left flank!","Sample: Hold the left flank!")}.get(app.ui_language)
    for y,line in zip((174,203),sample):
        preview.create_text(22,y,text=line,anchor="w",fill=TEXT,
                            font=(FONT,11,"bold"))
    actions=tk.Frame(right,bg=CARD)
    actions.pack(fill="x")
    for label,fn in (("test",app.test_overlay),("clear",app.clear_overlay),
                     ("standard",app.reset_overlay_position)):
        action(actions,tr(app,label),fn).pack(side="left",padx=(0,7),pady=3)
    edit=action(right,{"ru":"Изменить положение","uk":"Змінити положення",
                       "en":"Change position"}.get(app.ui_language,"Change position"),
                app.toggle_overlay_edit)
    edit.pack(anchor="w",pady=(8,4))
    app.overlay_edit_button_alt=edit
    row=tk.Frame(right,bg=CARD)
    row.pack(fill="x",pady=(4,0))
    for title,fn in (("borderless",app.enable_cod2_borderless),
                     ("screenshot",app.capture_game_screenshot)):
        action(row,tr(app,title),fn).pack(side="left",padx=(0,7))
