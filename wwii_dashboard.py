"""Approved WWII metal/tactical interface, using real existing CoD2 controls.

Style is derived from the user's confirmed second concept. The hero and
plate graphics contain NO UI state; all labels and actions are real Tk widgets.
"""
from __future__ import annotations
import math
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
        image=ui_photo(parent,"switch_off.png"),
        selectimage=ui_photo(parent,"switch_on.png"),
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
        header=tk.Canvas(outer,height=124,bg="#17130E",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        hero=ui_photo(header,"hero.png")
        brand=ui_photo(header,"brand_logo_compact.png")
        plaque=ui_photo(header,"version_plate.png")
        header.create_image(0,-28,anchor="nw",image=hero)
        header.create_image(11,2,anchor="nw",image=brand)
        header.create_text(406,113,text=tr(app,"tagline"),anchor="w",
                           fill="#EED6A7",font=(FONT,9,"bold"))
        header.create_line(0,122,1600,122,fill="#BC8A46",width=2)
        # Decor: a hand-drawn metallic insignia, not an online/health signal.
        emblem=[]
        for n in range(10):
            theta=-math.pi/2 + n*math.pi/5
            radius=20 if n%2==0 else 8
            emblem.extend((760+radius*math.cos(theta),
                           55+radius*math.sin(theta)))
        header.create_polygon(emblem,fill="#CCAA70",
                              outline="#684B2B",width=2)
        header.create_oval(742,37,778,73,outline="#5D4225",width=1)
        self.version_plate=header.create_image(0,0,image=plaque,anchor="ne")
        self.banner_version=header.create_text(0,0,text="",
            font=(FONT,11,"bold"),fill="#F8E0AE",anchor="e")
        def resize_header(event):
            header.coords(self.version_plate,event.width-9,8)
            header.coords(self.banner_version,event.width-22,28)
            header.itemconfigure(self.banner_version,
                                 text="v"+__import__("app").APP_VERSION)
        header.bind("<Configure>",resize_header)

        # Exactly the horizontal metal menu in the approved concept.
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
            button=tk.Button(nav,text=nav_name(app,name),image=photo,compound="left",
                command=callback,bg="#332C21",fg=TEXT,
                activebackground="#74400E",activeforeground="#FFF4D9",
                font=(FONT,self._nav_font_size,"bold"),bd=2,relief="raised",
                highlightthickness=1,highlightbackground="#775A35",
                highlightcolor="#FFC067",cursor="hand2",pady=3)
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
        footer=tk.Frame(outer,bg="#15130D",height=38,
                        highlightbackground="#9C7442",highlightthickness=2)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        first=tk.Frame(footer,bg="#15130D")
        first.pack(fill="x",padx=11,pady=5)
        text(first,"●",color=GREEN,bg="#15130D",size=10).pack(side="left")
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

    def _home(self,page):
        # Keep the approved six-zone composition. Scroll only when monitor
        # height/DPI is insufficient; the status strip always stays visible.
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
            # Exclude decorative background from scroll bounds.
            required=max(content.winfo_reqheight(),scroll.winfo_height())
            scroll.configure(scrollregion=(0,0,scroll.winfo_width(),required))
            needed=content.winfo_reqheight()>scroll.winfo_height()+2
            if needed and not bar.winfo_manager():
                bar.pack(side="right",fill="y")
            elif not needed and bar.winfo_manager():
                bar.pack_forget()
        content.bind("<Configure>",adjust_scroll)
        scroll.bind("<Configure>",lambda e: (
            scroll.itemconfigure(item,width=e.width),adjust_scroll()))
        self.widgets.append(scroll)
        grid=tk.Frame(content,bg=BG)
        grid.pack(fill="x",padx=7,pady=3)
        grid.columnconfigure(0,weight=62,uniform="wwii")
        grid.columnconfigure(1,weight=38,uniform="wwii")
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
            frame.grid(row=row,column=col,sticky="nsew",padx=4,pady=2)
            builder(body)

    def _home_server(self,p):
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x",expand=True)
        art=tk.Label(row,image=ui_photo(p,"server_scene_thumb.png"),bg=CARD)
        art.pack(side="left",padx=(0,11))
        info=tk.Frame(row,bg=CARD)
        info.pack(side="left",fill="both",expand=True)
        tk.Label(info,text=FEATURED_SERVER.name,bg=CARD,fg=TEXT,
                 font=(FONT,12,"bold"),anchor="w").pack(fill="x")
        text(info,FEATURED_SERVER.subtitle,color=MUTED,size=9).pack(anchor="w",pady=(2,0))
        text(info,FEATURED_SERVER.address,color=AMBER,size=9,bold=True).pack(anchor="w",pady=(2,0))
        # A preset address does not prove that the game is connected.
        tk.Label(info,textvariable=self.server_var,bg=CARD,fg=MUTED,
                 font=(FONT,9),anchor="w").pack(fill="x",pady=(2,2))
        actions=tk.Frame(info,bg=CARD)
        actions.pack(fill="x")
        tactical_action(actions,tr(self.app,"connect"),
                        self.app._launch_featured_server,primary=True).pack(side="left",padx=(0,5))
        discord=tactical_action(actions,"Discord",self.app._open_featured_server_discord)
        discord.pack(side="left",padx=(0,5))
        if not FEATURED_SERVER.discord_url:discord.state(["disabled"])
        tactical_action(actions,tr(self.app,"server_settings"),
                        self.app.show_server_settings).pack(side="left")

    def _home_engine(self,p):
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x")
        status=tk.Frame(row,bg=CARD)
        status.pack(side="left",fill="both",expand=True)
        names=("engine","pack","cache","collect")
        for key in names:
            line=tk.Frame(status,bg=CARD)
            line.pack(fill="x",pady=0)
            bullet=tk.Label(line,text="●",bg=CARD,fg=MUTED,font=(FONT,10))
            bullet.pack(side="left",padx=(0,6))
            value=tk.Label(line,text="",bg=CARD,fg=TEXT,
                           font=(FONT,9),anchor="w")
            value.pack(side="left",fill="x")
            setattr(self,"engine_"+key+"_label",value)
            setattr(self,"engine_"+key+"_bullet",bullet)
        # Compact HUD and real knowledge action share the same row;
        # the right panel no longer forces an extra 30px of vertical height.
        side=tk.Frame(row,bg=CARD)
        side.pack(side="right",padx=(6,0))
        hud=tk.Canvas(side,width=92,height=54,bg=CARD,
                      highlightthickness=0,borderwidth=0)
        hud.pack(anchor="center")
        hud.create_oval(26,1,76,51,outline="#776342",width=3)
        hud.create_arc(26,1,76,51,start=45,extent=265,
                       style="arc",outline="#C79B4C",width=3)
        hud.create_oval(34,9,68,43,outline="#62533A",width=2)
        hud.create_text(51,26,text="V2",font=(FONT,12,"bold"),fill=AMBER)
        tactical_action(side,tr(self.app,"learn"),
                        lambda:self.navigate("knowledge")).pack(anchor="e")

    def _home_translation(self,p):
        # Compact 3-column form: individual F8/F9 switches, both directions,
        # style and slang flags, without conflating the F8 and F9 targets.
        layout=tk.Frame(p,bg=CARD)
        layout.pack(fill="x",expand=True)
        layout.columnconfigure(0,weight=0)
        layout.columnconfigure(1,weight=1)
        layout.columnconfigure(2,weight=0)
        modes=tk.Frame(layout,bg=CARD)
        modes.grid(row=0,column=0,sticky="nw",padx=(0,11))
        tactical_switch(modes,"F8",self.app.enabled_var,
                        self.app.toggle_enabled).pack(anchor="w",pady=1)
        tactical_switch(modes,"F9",self.app.outgoing_chat.enabled_var,
                        self.app._outgoing_enabled_changed).pack(anchor="w",pady=2)
        central=tk.Frame(layout,bg=CARD)
        central.grid(row=0,column=1,sticky="ew")
        languages=tk.Frame(central,bg=CARD)
        languages.pack(fill="x",pady=(0,1))
        text(languages,tr(self.app,"target")+":",color=MUTED,size=9).pack(side="left")
        from app import TARGET_LANGUAGES
        available=list(TARGET_LANGUAGES.keys())
        custom=self.app._custom_language_label()
        if custom:available.append(custom)
        self.app.language_combo=ttk.Combobox(
            languages,textvariable=self.app.target_name_var,values=available,
            state="readonly",width=14)
        self.app.language_combo.pack(side="left",padx=(5,6))
        self.app.language_combo.bind(
            "<<ComboboxSelected>>",lambda _e:self.app._persist_settings())
        tactical_action(languages,tr(self.app,"other"),
                        self.app.choose_custom_language).pack(side="left")
        line=tk.Frame(central,bg=CARD)
        line.pack(fill="x",pady=(1,0))
        text(line,tr(self.app,"style")+":",color=MUTED,size=9).pack(side="left")
        styles=[self.app._style_label(v) for v in ("clear","live","raw")]
        self.app.slang_style_var.set(self.app._style_label(
            self.app.config.get("slang_style","live")))
        styles_input=ttk.Combobox(line,textvariable=self.app.slang_style_var,
                                   values=styles,state="readonly",width=16)
        styles_input.pack(side="left",padx=(5,0))
        styles_input.bind("<<ComboboxSelected>>",
                          lambda _e:self.app._persist_settings())
        direction=tk.Frame(central,bg=CARD)
        direction.pack(fill="x",pady=(2,0))
        text(direction,"F9:",color=MUTED,size=9).pack(side="left")
        tk.Label(direction,textvariable=self.app.outgoing_chat.route_var,
                 bg=CARD,fg=AMBER,font=(FONT,9,"bold")).pack(side="left",padx=(6,0))
        tactical_action(direction,tr(self.app,"translation")+" →",
                        lambda:self.navigate("translation")).pack(side="right")
        options=tk.Frame(layout,bg=CARD)
        options.grid(row=0,column=2,sticky="ne",padx=(6,0))
        flags=[]
        for label,var,command in (
            ("slang",self.app.slang_var,self.app._persist_settings),
            ("dedupe",self.app.dedupe_var,self.app._persist_settings),
            ("original",self.app.show_original_var,self.app.toggle_original),
        ):
            widget=check(options,tr(self.app,label),var,command)
            widget.pack(anchor="w",pady=0)
            flags.append(widget)

        # High DPI + narrow windows: move the three flags BELOW the
        # language selectors, instead of clipping the "Other language"
        # button. This is a real rearrangement of native controls.
        layout_mode=[False]
        def fit_translation(event):
            # Use real requested widths, not a hardcoded DPI/window cutoff.
            # Keep the flags in a second row whenever all three columns
            # would clip the Other-language or style controls.
            required=(modes.winfo_reqwidth()+central.winfo_reqwidth()
                      +max(w.winfo_reqwidth() for w in flags)+28)
            narrow=event.width<required
            if narrow==layout_mode[0]:
                return
            layout_mode[0]=narrow
            options.grid_forget()
            if narrow:
                options.grid(row=1,column=0,columnspan=3,sticky="w",pady=(3,0))
                for control in flags:
                    control.pack_forget()
                    control.pack(side="left",padx=(0,12))
            else:
                options.grid(row=0,column=2,sticky="ne",padx=(6,0))
                for control in flags:
                    control.pack_forget()
                    control.pack(anchor="w",pady=0)
        layout.bind("<Configure>",fit_translation)

    def _home_overlay(self,p):
        row=tk.Frame(p,bg=CARD)
        row.pack(fill="x",expand=True)
        left=tk.Frame(row,bg=CARD)
        left.pack(side="left",fill="both",expand=True)
        for label,var,command in (
            ("enabled",self.app.enabled_var,self.app.toggle_enabled),
            ("bg_only",self.app.bg_only_var,self.app._background_only_changed),
            ("fade",self.app.fade_var,self.app._fade_changed),
            ("compact_bg",self.app.compact_bg_var,self.app._compact_background_changed),
        ):
            check(left,tr(self.app,label),var,command).pack(anchor="w",pady=0)
        scene=tk.Canvas(row,bg="#1A1813",height=77,width=97,
                        borderwidth=0,highlightthickness=0)
        scene.pack(side="right",padx=(8,0))
        scene.create_rectangle(4,4,93,73,outline="#90734A",width=2)
        for x1,y1,x2,y2 in ((11,18,11,11),(11,11,18,11),
                             (79,11,87,11),(87,11,87,18),
                             (11,59,11,67),(11,67,18,67),
                             (79,67,87,67),(87,59,87,67)):
            scene.create_line(x1,y1,x2,y2,fill="#D6A35E",width=2)
        scene.create_line(48,21,48,58,fill=AMBER,width=2)
        scene.create_line(30,39,66,39,fill=AMBER,width=2)
        scene.create_oval(44,35,52,43,outline=AMBER,width=2)
        tactical_action(p,tr(self.app,"overlay")+"  →",
                        lambda:self.navigate("overlay")).pack(anchor="e")

    def _home_overlay_prefs(self,p):
        for label,var,label_var,minimum,maximum,callback in (
            ("font_size",self.app.font_var,self.app.font_label_var,7,20,self.app._font_slider),
            ("opacity",self.app.bg_var,self.app.bg_label_var,0,90,self.app._background_slider),
            ("time",self.app.ttl_var,self.app.ttl_label_var,5,20,self.app._ttl_slider),
        ):
            row=tk.Frame(p,bg=CARD)
            row.pack(fill="x",pady=0)
            text(row,tr(self.app,label),color=MUTED,size=9).pack(side="left")
            tk.Label(row,textvariable=label_var,bg=CARD,fg=AMBER,
                     width=6,font=(FONT,9,"bold")).pack(side="right")
            slider=ttk.Scale(row,from_=minimum,to=maximum,orient="horizontal",
                             command=callback)
            slider.set(var.get())
            slider.pack(side="right",fill="x",expand=True,padx=(12,6))
        options=tk.Frame(p,bg=CARD)
        options.pack(fill="x",pady=(5,0))
        count_group=tk.Frame(options,bg=CARD)
        count_group.pack(side="left")
        from app import MIN_OVERLAY_MESSAGES,MAX_OVERLAY_MESSAGES
        text(count_group,tr(self.app,"messages")+":",color=MUTED,size=9).pack(side="left")
        amount=ttk.Combobox(
            count_group,values=list(range(MIN_OVERLAY_MESSAGES,MAX_OVERLAY_MESSAGES+1)),
            textvariable=self.app.max_messages_var,width=3,state="readonly")
        amount.pack(side="left",padx=(5,10))
        amount.bind("<<ComboboxSelected>>",
                    lambda _e:self.app._max_messages_changed())
        presets_group=tk.Frame(options,bg=CARD)
        presets_group.pack(side="left")
        at_high_dpi=float(self.root.tk.call("tk","scaling"))>=1.85
        short_standard={"ru":"Стандарт","uk":"Стандарт","en":"Default"}
        short_text={"ru":"Только текст","uk":"Лише текст","en":"Text only"}
        for label,callback in (
            ("text_only",self.app.text_only_preset),
            ("minimal",self.app.minimal_preset),
            ("readable",self.app.readable_preset),
            ("standard",self.app.reset_overlay_position),
        ):
            caption=tr(self.app,label)
            if at_high_dpi and label=="standard":
                caption=short_standard.get(self.app.ui_language,"Default")
            if at_high_dpi and label=="text_only":
                caption=short_text.get(self.app.ui_language,"Text only")
            tactical_action(presets_group,caption,callback).pack(
                side="left",padx=(0,4))

        # On 150%-sized text at narrow widths, put all four presets on
        # their own row instead of cropping the final preset at the edge.
        appearance_stacked=[False]
        def fit_presets(event):
            total=count_group.winfo_reqwidth()+presets_group.winfo_reqwidth()+6
            stacked=event.width<total
            if stacked==appearance_stacked[0]:
                return
            appearance_stacked[0]=stacked
            count_group.pack_forget()
            presets_group.pack_forget()
            if stacked:
                count_group.pack(anchor="w")
                presets_group.pack(anchor="w",pady=(4,0))
            else:
                count_group.pack(side="left")
                presets_group.pack(side="left")
        options.bind("<Configure>",fit_presets)

    def _home_quick(self,p):
        layout=tk.Frame(p,bg=CARD)
        layout.pack(fill="both",expand=True)
        for col in range(3):layout.columnconfigure(col,weight=1)
        controls=(
            ("test",self.app.test_overlay),
            ("clear",self.app.clear_overlay),
            ("configure",self.app.toggle_overlay_edit),
            ("screenshot",self.app.capture_game_screenshot),
            ("export",self.app._export_knowledge),
            ("updates",lambda:self.app.check_updates(manual=True)),
        )
        # Short labels prevent clipping at 1366x768 and on 125% DPI.
        short={
            "ru":{"test":"Тест оверлея","clear":"Очистить",
                  "configure":"Настроить","screenshot":"Снимок F10",
                  "export":"Экспорт базы","updates":"Обновления"},
            "uk":{"test":"Тест оверлею","clear":"Очистити",
                  "configure":"Налаштувати","screenshot":"Знімок F10",
                  "export":"Експорт бази","updates":"Оновлення"},
            "en":{"test":"Test overlay","clear":"Clear",
                  "configure":"Configure","screenshot":"Shot F10",
                  "export":"Export data","updates":"Updates"},
        }
        labels=short.get(self.app.ui_language,short["en"])
        quick_buttons=[]
        for i,(name,callback) in enumerate(controls):
            label=labels[name]
            button=tactical_action(layout,label,callback,
                                  primary=name=="test",icon=name)
            button.grid(row=i//3,column=i%3,sticky="nsew",padx=3,pady=4,ipady=2)
            quick_buttons.append(button)
            if name=="configure":
                self.app.overlay_edit_button=button

        # 3x2 on normal displays; 2x3 when actual widget measurements
        # show that high-DPI text cannot fit in the available panel.
        layout_columns=[3]
        def fit_actions(event):
            width_required=3*(max(w.winfo_reqwidth() for w in quick_buttons)+8)
            columns=3 if event.width>=width_required else 2
            if columns==layout_columns[0]:
                return
            layout_columns[0]=columns
            for column in range(3):
                layout.columnconfigure(column,weight=1 if column<columns else 0)
            for index,button in enumerate(quick_buttons):
                button.grid_configure(row=index//columns,column=index%columns)

        layout.bind("<Configure>",fit_actions)

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
                             font=(FONT,self._nav_font_size,"bold"))
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
