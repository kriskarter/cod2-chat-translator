"""Approved WWII metal/tactical interface, using real existing CoD2 controls.

Style is derived from the user's confirmed second concept. The hero and
plate graphics contain NO UI state; all labels and actions are real Tk widgets.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dashboard_ui import (
    Dashboard, BG, CARD, SIDEBAR, TEXT, MUTED, AMBER, GREEN, BORDER,
    FONT, tr, text, card, action, check, label_combo, ui_photo,
)
from server_catalog import FEATURED_SERVER


def nav_name(app, name):
    choices = {
        "ru":{"home":"Главное","knowledge":"База знаний","stats":"Статистика",
              "settings":"Настройки","updates":"Обновления","discord":"Discord","about":"О программе"},
        "uk":{"home":"Головна","knowledge":"База знань","stats":"Статистика",
              "settings":"Налаштування","updates":"Оновлення","discord":"Discord","about":"Про програму"},
        "en":{"home":"Home","knowledge":"Knowledge","stats":"Statistics",
              "settings":"Settings","updates":"Updates","discord":"Discord","about":"About"},
    }
    return choices.get(app.ui_language,choices["ru"])[name]


class WWIIDashboard(Dashboard):
    """Horizontal navigation / original illustrated header / metal controls."""

    def _build(self):
        app=self.app
        outer=tk.Frame(self.root,bg=BG)
        outer.pack(fill="both",expand=True)
        self.outer=outer
        header=tk.Canvas(outer,height=146,bg="#17130E",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        hero=ui_photo(header,"hero.png")
        header.create_image(0,0,anchor="nw",image=hero)
        # Brand typography is dynamic, not painted into the bitmap.
        header.create_text(213,59,text="CoD2",anchor="w",
            fill="#ECD1A2",font=("Impact",45,"bold"))
        header.create_text(440,42,text="CHAT",anchor="w",
            fill="#F6E4BF",font=("Bahnschrift SemiCondensed",21,"bold"))
        header.create_text(440,78,text="TRANSLATOR",anchor="w",
            fill="#F6E4BF",font=("Bahnschrift SemiCondensed",23,"bold"))
        header.create_text(440,112,text=tr(app,"tagline"),anchor="w",
            fill="#E3BE88",font=(FONT,11))
        header.create_line(0,144,1600,144,fill="#AD7335",width=3)
        self.banner_version=header.create_text(1320,55,text="",anchor="e",
            font=(FONT,13,"bold"),fill="#F5E5C5")
        header.create_text(775,48,text="★",fill="#E6CE9C",
            font=("Segoe UI Symbol",45,"bold"))
        def resize_header(event):
            header.coords(self.banner_version,event.width-23,43)
            header.itemconfigure(self.banner_version,text="v"+__import__("app").APP_VERSION)
        header.bind("<Configure>",resize_header)

        # Exactly the horizontal metal menu in the approved concept.
        nav_shell=tk.Frame(outer,bg="#89633D",pady=2)
        nav_shell.pack(fill="x")
        nav=tk.Frame(nav_shell,bg=SIDEBAR)
        nav.pack(fill="x")
        buttons=[
            ("home",lambda:self.navigate("home")),
            ("knowledge",lambda:self.navigate("knowledge")),
            ("stats",lambda:self.navigate("stats")),
            ("settings",lambda:self.navigate("settings")),
            ("updates",lambda:app.check_updates(manual=True)),
            ("discord",app._open_featured_server_discord),
            ("about",app.show_about),
        ]
        for index,(name,callback) in enumerate(buttons):
            nav.columnconfigure(index,weight=1,uniform="nav")
            photo=ui_photo(nav,"nav_"+name+".png")
            button=tk.Button(nav,text=nav_name(app,name),image=photo,compound="left",
                command=callback,bg="#332C21",fg=TEXT,
                activebackground="#74400E",activeforeground="#FFF4D9",
                font=(FONT,11,"bold"),bd=2,relief="raised",
                highlightthickness=1,highlightbackground="#775A35",
                highlightcolor="#FFC067",cursor="hand2",pady=9)
            button.grid(row=0,column=index,sticky="nsew",padx=2,pady=2)
            self.nav_buttons[name]=button
            if name=="discord" and not FEATURED_SERVER.discord_url:
                button.configure(state="disabled")

        stack=tk.Frame(outer,bg=BG)
        stack.pack(fill="both",expand=True)
        self.stack=stack
        for name in ("home","translation","overlay","knowledge","stats","settings"):
            page=tk.Frame(stack,bg=BG)
            page.place(relx=0,rely=0,relwidth=1,relheight=1)
            self.pages[name]=page
        self._home(self.pages["home"])
        self._translation(self.pages["translation"])
        self._overlay(self.pages["overlay"])
        self._knowledge(self.pages["knowledge"])
        self._stats(self.pages["stats"])
        self._settings(self.pages["settings"])
        if app.overlay_editing:
            for key in ("overlay_edit_button","overlay_edit_button_alt"):
                widget=getattr(app,key,None)
                if widget:widget.configure(text=app.t("lock_overlay"))
        for page in self.pages.values():self._enable_page_wheel(page)
        footer=tk.Frame(outer,bg="#15130D",height=60,
                        highlightbackground="#88643A",highlightthickness=2)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        first=tk.Frame(footer,bg="#15130D")
        first.pack(fill="x",padx=17,pady=(4,0))
        text(first,"●",color=GREEN,bg="#15130D",size=13).pack(side="left")
        self.footer_engine=text(first,"",bg="#15130D",color=AMBER,bold=True)
        self.footer_engine.pack(side="left",padx=(7,22))
        self.footer_base=text(first,"",bg="#15130D",color=TEXT,size=9)
        self.footer_base.pack(side="left",padx=(8,20))
        self.footer_style=text(first,"",bg="#15130D",color=AMBER,size=9)
        self.footer_style.pack(side="left",padx=8)
        tk.Label(first,textvariable=app.status_var,bg="#15130D",fg=TEXT,
                 font=(FONT,9),anchor="e").pack(side="right",fill="x",expand=True)
        tk.Label(footer,textvariable=app.last_var,bg="#15130D",fg=MUTED,
                 font=(FONT,8),anchor="w").pack(fill="x",padx=18)
        self.navigate("home")

    def _home(self,page):
        # Keep the approved six-zone composition. Scroll only when monitor
        # height/DPI is insufficient; the status strip always stays visible.
        scroll=tk.Canvas(page,bg=BG,highlightthickness=0,borderwidth=0)
        bar=ttk.Scrollbar(page,orient="vertical",command=scroll.yview)
        scroll.configure(yscrollcommand=bar.set)
        bar.pack(side="right",fill="y")
        scroll.pack(side="left",fill="both",expand=True)
        content=tk.Frame(scroll,bg=BG)
        item=scroll.create_window((0,0),window=content,anchor="nw")
        content.bind("<Configure>",lambda _e:scroll.configure(scrollregion=scroll.bbox("all")))
        scroll.bind("<Configure>",lambda e:scroll.itemconfigure(item,width=e.width))
        self.widgets.append(scroll)
        grid=tk.Frame(content,bg=BG)
        grid.pack(fill="x",padx=12,pady=10)
        grid.columnconfigure(0,weight=63,uniform="wwii")
        grid.columnconfigure(1,weight=37,uniform="wwii")
        for i in range(3):grid.rowconfigure(i,weight=1)
        blocks=[
            (0,0,{"ru":"СЕРВЕР","uk":"СЕРВЕР","en":"SERVER"}.get(self.app.ui_language,"SERVER"),self._home_server),
            (0,1,"SMART ENGINE V2",self._home_engine),
            (1,0,tr(self.app,"translation").upper()+" · F8 / F9",self._home_translation),
            (1,1,tr(self.app,"overlay_view").upper(),self._home_overlay),
            (2,0,tr(self.app,"overlay_head").upper(),self._home_overlay_prefs),
            (2,1,tr(self.app,"quick").upper(),self._home_quick),
        ]
        for row,col,title,builder in blocks:
            frame,body=card(grid,title)
            frame.grid(row=row,column=col,sticky="nsew",padx=6,pady=6)
            builder(body)

    def _home_server(self,p):
        layout=tk.Frame(p,bg=CARD)
        layout.pack(fill="both",expand=True)
        photo=ui_photo(p,"server_scene.png")
        scene=tk.Label(layout,image=photo,bg=CARD)
        scene.pack(side="left",padx=(0,12))
        info=tk.Frame(layout,bg=CARD)
        info.pack(side="left",fill="both",expand=True)
        tk.Label(info,text=FEATURED_SERVER.name,bg=CARD,fg=TEXT,
                 font=(FONT,14,"bold")).pack(anchor="w",pady=(2,3))
        text(info,FEATURED_SERVER.subtitle,color=MUTED,size=9).pack(anchor="w")
        text(info,FEATURED_SERVER.address,color=AMBER,bold=True).pack(anchor="w",pady=(5,4))
        # Never call a preset address "connected" without a real signal.
        tk.Label(info,textvariable=self.server_var,bg=CARD,fg=MUTED,
                 font=(FONT,9,"bold")).pack(anchor="w")
        row=tk.Frame(info,bg=CARD)
        row.pack(anchor="w",pady=(8,0))
        action(row,tr(self.app,"connect"),self.app._launch_featured_server,primary=True).pack(side="left",padx=(0,6))
        discord=action(row,"Discord",self.app._open_featured_server_discord)
        discord.pack(side="left",padx=(0,6))
        if not FEATURED_SERVER.discord_url:discord.state(["disabled"])
        action(row,tr(self.app,"server_settings"),self.app.show_server_settings).pack(side="left")

    def _home_engine(self,p):
        vals=tk.Frame(p,bg=CARD)
        vals.pack(fill="x")
        for name,key in (
            ("engine","smart_engine_var"),("pack","_knowledge_runtime"),
            ("cache","config"),("collect","config"),
        ):
            row=tk.Frame(vals,bg=CARD)
            row.pack(fill="x",pady=2)
            bullet=tk.Label(row,text="●",fg=GREEN,bg=CARD,font=(FONT,11))
            bullet.pack(side="left",padx=(0,7))
            label=tk.Label(row,fg=TEXT,bg=CARD,font=(FONT,10),anchor="w")
            label.pack(side="left",fill="x")
            setattr(self,"engine_"+name+"_label",label)
            setattr(self,"engine_"+name+"_bullet",bullet)
        action(p,tr(self.app,"learn"),lambda:self.navigate("knowledge")).pack(anchor="e",pady=(7,0))

    def _home_translation(self,p):
        top=tk.Frame(p,bg=CARD)
        top.pack(fill="x")
        check(top,tr(self.app,"f8_label"),self.app.enabled_var,self.app.toggle_enabled).pack(side="left",padx=(0,10))
        check(top,tr(self.app,"f9_label"),self.app.outgoing_chat.enabled_var,
              self.app._outgoing_enabled_changed).pack(side="left")
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x",pady=(8,0))
        text(row,tr(self.app,"target")+":",color=MUTED).pack(side="left")
        from app import TARGET_LANGUAGES
        items=list(TARGET_LANGUAGES.keys())
        custom=self.app._custom_language_label()
        if custom:items.append(custom)
        self.app.language_combo=ttk.Combobox(row,textvariable=self.app.target_name_var,
            values=items,state="readonly",width=14)
        self.app.language_combo.pack(side="left",padx=(7,10))
        self.app.language_combo.bind("<<ComboboxSelected>>",
                                     lambda _e:self.app._persist_settings())
        action(row,tr(self.app,"other"),self.app.choose_custom_language).pack(side="left")
        check(row,tr(self.app,"slang"),self.app.slang_var,self.app._persist_settings).pack(side="right")
        bottom=tk.Frame(p,bg=CARD)
        bottom.pack(fill="x",pady=(8,0))
        text(bottom,tr(self.app,"style")+":",color=MUTED).pack(side="left")
        style_names=[self.app._style_label(x) for x in ("clear","live","raw")]
        self.app.slang_style_var.set(self.app._style_label(self.app.config.get("slang_style","live")))
        style_combo=ttk.Combobox(bottom,textvariable=self.app.slang_style_var,values=style_names,
                     width=16,state="readonly")
        style_combo.pack(side="left",padx=(8,8))
        style_combo.bind("<<ComboboxSelected>>",lambda _e:self.app._persist_settings())
        check(bottom,tr(self.app,"dedupe"),self.app.dedupe_var,self.app._persist_settings).pack(side="left",padx=5)
        check(bottom,tr(self.app,"original"),self.app.show_original_var,self.app.toggle_original).pack(side="left",padx=5)
        action(p,tr(self.app,"translation")+"  →",lambda:self.navigate("translation")).pack(anchor="e",pady=(6,0))

    def _home_overlay(self,p):
        for key,var,command in (
            ("enabled",self.app.enabled_var,self.app.toggle_enabled),
            ("bg_only",self.app.bg_only_var,self.app._background_only_changed),
            ("fade",self.app.fade_var,self.app._fade_changed),
            ("compact_bg",self.app.compact_bg_var,self.app._compact_background_changed),
        ):
            check(p,tr(self.app,key),var,command).pack(anchor="w",pady=1)
        action(p,tr(self.app,"overlay")+"  →",lambda:self.navigate("overlay")).pack(anchor="e",pady=(4,0))

    def _home_overlay_prefs(self,p):
        for title,value_var,label_var,minimum,maximum,cb in (
            ("font_size",self.app.font_var,self.app.font_label_var,7,20,self.app._font_slider),
            ("opacity",self.app.bg_var,self.app.bg_label_var,0,90,self.app._background_slider),
            ("time",self.app.ttl_var,self.app.ttl_label_var,5,20,self.app._ttl_slider),
        ):
            row=tk.Frame(p,bg=CARD)
            row.pack(fill="x",pady=3)
            text(row,tr(self.app,title),size=9,color=MUTED).pack(side="left")
            tk.Label(row,textvariable=label_var,bg=CARD,fg=AMBER,width=6).pack(side="right")
            scale=ttk.Scale(row,from_=minimum,to=maximum,
                            orient="horizontal",command=cb)
            scale.set(value_var.get())
            scale.pack(side="right",fill="x",expand=True,padx=(12,8))
        presets=tk.Frame(p,bg=CARD)
        presets.pack(fill="x",pady=(7,0))
        for label,command in (
            ("text_only",self.app.text_only_preset),("minimal",self.app.minimal_preset),
            ("readable",self.app.readable_preset),("standard",self.app.reset_overlay_position),
        ):
            action(presets,tr(self.app,label),command).pack(side="left",padx=(0,6))

    def _home_quick(self,p):
        buttons=(
            ("test",self.app.test_overlay),("clear",self.app.clear_overlay),
            ("configure",self.app.toggle_overlay_edit),
            ("screenshot",self.app.capture_game_screenshot),
            ("export",self.app._export_knowledge),
            ("updates",lambda:self.app.check_updates(manual=True)),
        )
        layout=tk.Frame(p,bg=CARD)
        layout.pack(fill="both",expand=True)
        for col in range(3):layout.columnconfigure(col,weight=1)
        for idx,(name,command) in enumerate(buttons):
            label=nav_name(self.app,"updates") if name=="updates" else tr(self.app,name)
            button=action(layout,label,command,primary=(name=="test"))
            button.grid(row=idx//3,column=idx%3,sticky="nsew",padx=4,pady=6,ipady=4)
            if name=="configure":
                self.app.overlay_edit_button=button

    def navigate(self,name):
        if name not in self.pages:return False
        self.page=name
        self.pages[name].tkraise()
        if name=="stats":self.request_stats()
        for key,button in self.nav_buttons.items():
            if button.cget("state")=="disabled":continue
            active=key==name
            button.configure(bg="#9B4A07" if active else "#332C21",
                             fg="#FFF6E7" if active else TEXT,
                             activebackground="#BB6713",
                             font=(FONT,11,"bold"))
        return True

    def refresh(self):
        super().refresh()
        # Both engines and data flags are displayed from source variables.
        if not hasattr(self,"engine_engine_label"):return
        app=self.app
        active=bool(app.smart_engine_var.get())
        runtime=getattr(app,"_knowledge_runtime",None)
        kb=runtime.version if (runtime and runtime.enabled) else 0
        labels={
            "engine":("Smart V2" if active and kb else "Smart V1" if active else "Classic"),
            "pack":f"{tr(app,'knowledge_state')}: v{kb}" if kb else tr(app,"knowledge_state")+": —",
            "cache":({"ru":"Локальный кэш: ","uk":"Локальний кеш: ","en":"Local cache: "}.get(app.ui_language,"Local cache: ") + ("ON" if app.config.get("experience_cache") else "OFF")),
            "collect":({"ru":"Сбор примеров: ","uk":"Збирання прикладів: ","en":"Example collection: "}.get(app.ui_language,"Example collection: ") + ("ON" if app.config.get("experience_collect") else "OFF")),
        }
        for key,value in labels.items():
            label=getattr(self,"engine_"+key+"_label",None)
            bullet=getattr(self,"engine_"+key+"_bullet",None)
            healthy={
                "engine":active,
                "pack":bool(kb),
                "cache":bool(app.config.get("experience_cache")),
                "collect":bool(app.config.get("experience_collect")),
            }[key]
            if label is not None and label.winfo_exists():
                label.configure(text=value)
            if bullet is not None and bullet.winfo_exists():
                bullet.configure(fg=GREEN if healthy else MUTED)
        runtime=getattr(app,"_knowledge_runtime",None)
        self.footer_base.configure(text=(f"{runtime.pack.count} {tr(app,'base').lower()}" if kb and runtime else "Knowledge: —"))
        self.footer_style.configure(text=tr(app,"style")+": "+str(app.slang_style_var.get()))


def build_dashboard(app):
    app._update_overlay_hotkey_status()
    app.dashboard=WWIIDashboard(app)
