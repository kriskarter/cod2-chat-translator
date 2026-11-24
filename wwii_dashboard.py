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


def tactical_action(parent, caption, command, *, primary=False, icon=None):
    """Real native button with amber metal states, not a painted hotspot."""
    button=ttk.Button(
        parent,text=caption,command=command,
        style="TacticalAccent.TButton" if primary else "Tactical.TButton",
    )
    if icon:
        button.configure(image=ui_photo(parent,"quick_"+icon+".png"),
                         compound="left")
    return button


def tactical_switch(parent, caption, var, command):
    """A keyboard-accessible checkbutton with checked/unchecked art.

    The image is a state indicator; the actual BooleanVar/command remains
    the same as the existing F8/F9/overlay settings.
    """
    return tk.Checkbutton(
        parent,text=caption,variable=var,command=command,indicatoron=0,
        image=ui_photo(parent,"premium_switch_off.png"),
        selectimage=ui_photo(parent,"premium_switch_on.png"),
        compound="left",bg=CARD,fg=TEXT,selectcolor=CARD,
        activebackground=CARD,activeforeground=TEXT,
        padx=1,pady=0,bd=0,relief="flat",overrelief="flat",
        font=(FONT,9,"bold"),cursor="hand2",takefocus=True,
        highlightthickness=1,highlightbackground=CARD,
        highlightcolor=AMBER,
    )


class WWIIDashboard(Dashboard):
    """Horizontal navigation / original illustrated header / metal controls."""

    def _build(self):
        app=self.app
        outer=tk.Frame(self.root,bg=BG)
        outer.pack(fill="both",expand=True)
        self.outer=outer
        # The brand is a separate, transparent, metallic raster asset built
        # from original artwork. Only the version and localized subtitle
        # are live text. The photographic hero contains no fake UI states.
        header=tk.Canvas(outer,height=137,bg="#17130E",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        hero=ui_photo(header,"premium_hero.png")
        brand=ui_photo(header,"premium_logo.png")
        plaque=ui_photo(header,"version_plate.png")
        header.create_image(0,0,anchor="nw",image=hero)
        header.create_image(205,4,anchor="nw",image=brand)
        header.create_text(229,120,text=tr(app,"tagline"),anchor="w",
                           fill="#EED6A7",font=(FONT,9,"bold"))
        header.create_line(0,135,1600,135,fill="#BC8A46",width=2)
        self.version_plate=header.create_image(0,0,image=plaque,anchor="ne")
        self.banner_version=header.create_text(0,0,text="",
            font=(FONT,11,"bold"),fill="#F8E0AE",anchor="e")
        def resize_header(event):
            header.coords(self.version_plate,event.width-9,8)
            header.coords(self.banner_version,event.width-22,28)
            header.itemconfigure(self.banner_version,
                                 text="v"+__import__("app").APP_VERSION)
        header.bind("<Configure>",resize_header)

        # The seven actions are real ttk buttons on stretchable illustrated
        # surfaces; focus, disabled state and mouse states are live.
        nav_shell=tk.Frame(outer,bg="#89633D",pady=1)
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
        # At 125%/150% DPI use proportionally smaller typography so all
        # seven real navigation buttons fit without clipped labels.
        dpi_scale=float(self.root.tk.call("tk","scaling"))
        self._nav_font_size=9 if dpi_scale>=1.85 else 10 if dpi_scale>=1.6 else 11
        for index,(name,callback) in enumerate(buttons):
            nav.columnconfigure(index,weight=1,uniform="nav")
            photo=ui_photo(nav,"nav_"+name+".png")
            button=ttk.Button(nav,text=nav_name(app,name),image=photo,compound="left",
                command=callback,style="PremiumNav.TButton",cursor="hand2")
            button.grid(row=0,column=index,sticky="nsew",padx=1,pady=1)
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
        footer=tk.Frame(outer,bg="#15130D",height=40,
                        highlightbackground="#9C7442",highlightthickness=2)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        first=tk.Frame(footer,bg="#15130D")
        first.pack(fill="x",padx=11,pady=5)
        self.footer_ready_dot=text(first,"●",color=MUTED,
                                   bg="#15130D",size=10)
        self.footer_ready_dot.pack(side="left")
        self.footer_engine=text(first,"",bg="#15130D",color=AMBER,bold=True,size=9)
        self.footer_engine.pack(side="left",padx=(6,19))
        self.footer_base=text(first,"",bg="#15130D",color=TEXT,size=9)
        self.footer_base.pack(side="left",padx=(5,18))
        self.footer_style=text(first,"",bg="#15130D",color=AMBER,size=9)
        self.footer_style.pack(side="left",padx=5)
        # status_var is the REAL latest application event, not decorative
        # fake latency. Any long message is clipped to its allocated width.
        tk.Label(first,textvariable=app.status_var,bg="#15130D",fg=TEXT,
                 font=(FONT,9),anchor="e",width=40).pack(side="right")
        self.navigate("home")

    def _home(self, page):
        """Beginner-friendly home: five focused panels, advanced controls in tabs.

        The loaded settings stay untouched. No preset reset or 'beginner'
        override is applied when the Home page opens.
        """
        scroll=tk.Canvas(page,bg=BG,highlightthickness=0,borderwidth=0)
        bar=ttk.Scrollbar(page,orient="vertical",command=scroll.yview)
        scroll.configure(yscrollcommand=bar.set)
        scroll.pack(side="left",fill="both",expand=True)
        scroll.create_image(0,0,anchor="nw",
                            image=ui_photo(scroll,"body_backdrop.png"),
                            tags="backdrop")
        content=tk.Frame(scroll,bg=BG)
        self.home_canvas=scroll
        self.home_content=content
        self.home_scrollbar=bar
        item=scroll.create_window((0,0),window=content,anchor="nw")
        def adjust_scroll(_event=None):
            required=max(content.winfo_reqheight(),scroll.winfo_height())
            scroll.configure(scrollregion=(0,0,scroll.winfo_width(),required))
            needed=content.winfo_reqheight()>scroll.winfo_height()+2
            if needed and not bar.winfo_manager():
                bar.pack(side="right",fill="y")
            elif not needed and bar.winfo_manager():
                bar.pack_forget()
        content.bind("<Configure>",adjust_scroll)
        scroll.bind("<Configure>",lambda e:(
            scroll.itemconfigure(item,width=e.width),adjust_scroll()))
        self.widgets.append(scroll)

        grid=tk.Frame(content,bg=BG)
        grid.pack(fill="x",padx=7,pady=(4,2))
        grid.columnconfigure(0,weight=60,uniform="wwii")
        grid.columnconfigure(1,weight=40,uniform="wwii")

        titles={
            "ru":("СЕРВЕР","ПЕРЕВОД ЧАТА · F8 / F9","ОВЕРЛЕЙ В ИГРЕ","БЫСТРЫЕ ДЕЙСТВИЯ"),
            "uk":("СЕРВЕР","ПЕРЕКЛАД ЧАТУ · F8 / F9","ОВЕРЛЕЙ У ГРІ","ШВИДКІ ДІЇ"),
            "en":("SERVER","CHAT TRANSLATION · F8 / F9","IN-GAME OVERLAY","QUICK ACTIONS"),
        }
        server_title,translation_title,overlay_title,quick_title=titles.get(
            self.app.ui_language,titles["en"])
        blocks=(
            (0,0,1,server_title,self._home_server),
            (0,1,1,"SMART ENGINE",self._home_engine),
            (1,0,1,translation_title,self._home_translation),
            (1,1,1,overlay_title,self._home_overlay),
            (2,0,2,quick_title,self._home_quick),
        )
        for row,col,colspan,title,builder in blocks:
            frame,body=card(grid,title)
            frame.grid(row=row,column=col,columnspan=colspan,sticky="nsew",
                       padx=4,pady=4)
            builder(body)

    def _home_server(self,p):
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x")
        tk.Label(row,image=ui_photo(p,"premium_server.png"),
                 bg=CARD).pack(side="left",padx=(0,12))
        info=tk.Frame(row,bg=CARD)
        info.pack(side="left",fill="both",expand=True)
        tk.Label(info,text=FEATURED_SERVER.name,bg=CARD,fg=TEXT,
                 font=(FONT,13,"bold"),anchor="w").pack(anchor="w")
        text(info,FEATURED_SERVER.subtitle,color=MUTED,size=9).pack(anchor="w",pady=(2,0))
        text(info,FEATURED_SERVER.address,color=AMBER,size=10,bold=True).pack(anchor="w",pady=(4,0))
        # The selected server profile is not the same as being connected.
        tk.Label(info,textvariable=self.server_var,bg=CARD,fg=MUTED,
                 font=(FONT,9),anchor="w").pack(anchor="w",pady=(2,4))
        actions=tk.Frame(info,bg=CARD)
        actions.pack(anchor="w")
        tactical_action(actions,tr(self.app,"connect"),
                        self.app._launch_featured_server,primary=True).pack(
                            side="left",padx=(0,7))
        discord=tactical_action(actions,"Discord",self.app._open_featured_server_discord)
        discord.pack(side="left")
        if not FEATURED_SERVER.discord_url:discord.state(["disabled"])
        # Server profiles are accessible in the real Settings page;
        # no separate server settings button on beginner Home.

    def _home_engine(self,p):
        # Real engine/pack status, no artificial green "healthy" lights.
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x")
        detail=tk.Frame(row,bg=CARD)
        detail.pack(side="left",fill="x",expand=True)
        line=tk.Frame(detail,bg=CARD)
        line.pack(anchor="w")
        self.engine_engine_bullet=tk.Label(line,text="●",bg=CARD,
                                            fg=MUTED,font=(FONT,12))
        self.engine_engine_bullet.pack(side="left",padx=(0,7))
        self.engine_engine_label=tk.Label(line,text="",bg=CARD,fg=TEXT,
                                           font=(FONT,12,"bold"),anchor="w")
        self.engine_engine_label.pack(side="left")
        self.engine_pack_label=tk.Label(detail,text="",bg=CARD,fg=MUTED,
                                         font=(FONT,9),anchor="w")
        self.engine_pack_label.pack(anchor="w",pady=(5,0))
        side=tk.Frame(row,bg=CARD)
        side.pack(side="right")
        hud=tk.Canvas(side,width=75,height=62,bg=CARD,
                      highlightthickness=0,borderwidth=0)
        hud.pack(anchor="center")
        hud.create_oval(10,3,64,57,outline="#80653A",width=3)
        hud.create_arc(10,3,64,57,start=60,extent=245,
                       style="arc",outline="#CF9F45",width=3)
        hud.create_text(37,30,text="AI",fill=AMBER,font=(FONT,15,"bold"))
        tactical_action(p,tr(self.app,"learn"),
                        lambda:self.navigate("knowledge")).pack(anchor="e",pady=(5,0))

    def _home_translation(self,p):
        # F8 and F9 stay independent; all expert controls are in Translation.
        left=tk.Frame(p,bg=CARD)
        left.pack(fill="x",pady=(2,8))
        flags=tk.Frame(left,bg=CARD)
        flags.pack(side="left",padx=(0,20))
        if self.app.ui_language=="ru":
            incoming,outgoing="Входящий чат","Исходящий чат"
        elif self.app.ui_language=="uk":
            incoming,outgoing="Вхідний чат","Вихідний чат"
        else:
            incoming,outgoing="Incoming chat","Outgoing chat"
        tactical_switch(flags,"F8  "+incoming,
                        self.app.enabled_var,self.app.toggle_enabled).pack(
                            anchor="w",pady=(1,5))
        tactical_switch(flags,"F9  "+outgoing,
                        self.app.outgoing_chat.enabled_var,
                        self.app._outgoing_enabled_changed).pack(anchor="w")
        routes=tk.Frame(left,bg=CARD)
        routes.pack(side="left",fill="x",expand=True)
        row=tk.Frame(routes,bg=CARD)
        row.pack(fill="x",pady=(1,4))
        text(row,tr(self.app,"target")+":",color=MUTED,size=9).pack(side="left")
        from app import TARGET_LANGUAGES
        available=list(TARGET_LANGUAGES.keys())
        custom=self.app._custom_language_label()
        if custom:available.append(custom)
        self.app.language_combo=ttk.Combobox(
            row,textvariable=self.app.target_name_var,values=available,
            state="readonly",width=16)
        self.app.language_combo.pack(side="left",padx=(8,0))
        self.app.language_combo.bind("<<ComboboxSelected>>",
                                     lambda _e:self.app._persist_settings())
        route=tk.Frame(routes,bg=CARD)
        route.pack(fill="x")
        text(route,"F9:",color=MUTED,size=9).pack(side="left")
        tk.Label(route,textvariable=self.app.outgoing_chat.route_var,
                 bg=CARD,fg=AMBER,font=(FONT,10,"bold")).pack(side="left",padx=8)
        label={
            "ru":"Расширенные настройки перевода",
            "uk":"Розширені налаштування перекладу",
            "en":"Advanced translation settings",
        }.get(self.app.ui_language,"Advanced translation settings")
        tactical_action(p,label,lambda:self.navigate("translation")).pack(
            anchor="e",pady=(2,0))

    def _home_overlay(self,p):
        # Only the basic enable control appears on Home. All advanced
        # display options and the four presets live on the Overlay page.
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x")
        left=tk.Frame(row,bg=CARD)
        left.pack(side="left",fill="both",expand=True,pady=(10,0))
        overlay_switch={"ru":"Перевод F8 и оверлей", "uk":"Переклад F8 й оверлей",
                        "en":"F8 translation and overlay"}
        tactical_switch(left,overlay_switch.get(self.app.ui_language,
                                                overlay_switch["en"]),
                        self.app.enabled_var,self.app.toggle_enabled).pack(anchor="w")
        text(left,tr(self.app,"overlay_hint"),color=MUTED,size=9,
             wraplength=240).pack(anchor="w",pady=(6,0))
        scene=tk.Canvas(row,bg="#1A1813",height=72,width=94,
                        borderwidth=0,highlightthickness=0)
        scene.pack(side="right",padx=(8,0))
        scene.create_image(0,0,anchor="nw",image=ui_photo(scene,"premium_overlay_preview.png"))
        scene.create_rectangle(4,4,90,68,outline="#90734A",width=2)
        for x1,y1,x2,y2 in ((11,18,11,11),(11,11,18,11),
                             (76,11,84,11),(84,11,84,18),
                             (11,55,11,63),(11,63,18,63),
                             (76,63,84,63),(84,55,84,63)):
            scene.create_line(x1,y1,x2,y2,fill="#D6A35E",width=2)
        scene.create_line(47,19,47,53,fill=AMBER,width=2)
        scene.create_line(30,36,64,36,fill=AMBER,width=2)
        scene.create_oval(43,32,51,40,outline=AMBER,width=2)
        label={
            "ru":"Настроить оверлей →",
            "uk":"Налаштувати оверлей →",
            "en":"Overlay settings →",
        }.get(self.app.ui_language,"Overlay settings →")
        tactical_action(p,label,lambda:self.navigate("overlay")).pack(anchor="e",pady=(6,0))

    def _home_quick(self,p):
        # Exactly three actions on Home. Secondary actions are not removed,
        # only discoverable via the native "More" menu.
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x")
        labels={
            "ru":("Тест оверлея","Снимок F10","Настроить","Ещё ▾",
                  "Очистить оверлей","Экспорт базы","Проверить обновления"),
            "uk":("Тест оверлею","Знімок F10","Налаштувати","Ще ▾",
                  "Очистити оверлей","Експорт бази","Перевірити оновлення"),
            "en":("Test overlay","Shot F10","Configure","More ▾",
                  "Clear overlay","Export knowledge","Check updates"),
        }
        test,shot,configure,more,clear,export,updates=labels.get(
            self.app.ui_language,labels["en"])
        tactical_action(row,test,self.app.test_overlay,
                        primary=True,icon="test").pack(side="left",padx=(0,7))
        tactical_action(row,shot,self.app.capture_game_screenshot,
                        icon="screenshot").pack(side="left",padx=(0,7))
        button=tactical_action(row,configure,self.app.toggle_overlay_edit,
                               icon="configure")
        button.pack(side="left")
        self.app.overlay_edit_button=button
        # All four controls share one row: no wasted bottom strip.
        extra_menu=tk.Menu(row,tearoff=False,bg="#33281D",fg=TEXT,
                           activebackground="#97510D",activeforeground="#FFFFFF",
                           borderwidth=1)
        extra_menu.add_command(label=clear,command=self.app.clear_overlay)
        extra_menu.add_command(label=export,command=self.app._export_knowledge)
        extra_menu.add_command(label=updates,
                               command=lambda:self.app.check_updates(manual=True))
        self.home_more_menu=extra_menu
        more_button=tactical_action(
            row,more,lambda:extra_menu.tk_popup(
                more_button.winfo_rootx(),
                more_button.winfo_rooty()+more_button.winfo_height()))
        more_button.pack(side="right",padx=(12,0))
        self.home_more_button=more_button

    def navigate(self,name):
        if name not in self.pages:return False
        self.page=name
        self.pages[name].tkraise()
        if name=="stats":self.request_stats()
        for key,button in self.nav_buttons.items():
            if button.instate(["disabled"]):continue
            active=key==name
            button.configure(style="PremiumNavActive.TButton" if active
                             else "PremiumNav.TButton")
        return True

    def refresh(self):
        super().refresh()
        if not hasattr(self,"engine_engine_label"):
            return
        app=self.app
        active=bool(app.smart_engine_var.get())
        runtime=getattr(app,"_knowledge_runtime",None)
        version=runtime.version if runtime and runtime.enabled else 0
        self.engine_engine_label.configure(
            text="Smart V2" if active and version else
                 "Smart V1" if active else "Classic")
        self.engine_engine_bullet.configure(fg=GREEN if active else MUTED)
        self.footer_ready_dot.configure(
            fg=GREEN if (app.enabled_var.get() or
                         app.outgoing_chat.enabled_var.get()) else MUTED)
        counts=runtime.pack.count if runtime and version else 0
        desc={
            "ru":f"База знаний: {counts} групп" if version else "База знаний: не загружена",
            "uk":f"База знань: {counts} груп" if version else "База знань: не завантажена",
            "en":f"Knowledge: {counts} groups" if version else "Knowledge: not loaded",
        }
        self.engine_pack_label.configure(text=desc.get(app.ui_language,desc["en"]))
        self.footer_base.configure(
            text="F9  "+str(app.outgoing_chat.route_var.get()))
        self.footer_style.configure(text="")


def build_dashboard(app):
    app._update_overlay_hotkey_status()
    app.dashboard=WWIIDashboard(app)
