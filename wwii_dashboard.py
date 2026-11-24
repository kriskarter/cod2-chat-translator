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
        "ru":{"home":"Главное","translation":"Перевод","overlay":"Оверлей",
              "knowledge":"База знаний","stats":"Статистика",
              "settings":"Настройки","updates":"Обновления","discord":"Discord","about":"О программе"},
        "uk":{"home":"Головна","translation":"Переклад","overlay":"Оверлей",
              "knowledge":"База знань","stats":"Статистика",
              "settings":"Налаштування","updates":"Оновлення","discord":"Discord","about":"Про програму"},
        "en":{"home":"Home","translation":"Translation","overlay":"Overlay",
              "knowledge":"Knowledge","stats":"Statistics",
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
        compact_dpi=float(self.root.tk.call("tk","scaling"))>=1.6
        outer=tk.Frame(self.root,bg=BG)
        outer.pack(fill="both",expand=True)
        self.outer=outer
        # The brand is a separate, transparent, metallic raster asset built
        # from original artwork. Only the version and localized subtitle
        # are live text. The photographic hero contains no fake UI states.
        header_height=132 if compact_dpi else 148
        header=tk.Canvas(outer,height=header_height,bg="#17130E",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        hero=ui_photo(header,"premium_hero.png")
        brand=ui_photo(header,"premium_logo_compact.png" if compact_dpi
                       else "premium_logo.png")
        plaque=ui_photo(header,"version_plate.png")
        header.create_image(0,0,anchor="nw",image=hero)
        header.create_image(170 if compact_dpi else 195,1,anchor="nw",image=brand)
        header.create_text(200 if compact_dpi else 225,
                           122 if compact_dpi else 139,
                           text=tr(app,"tagline"),anchor="w",
                           fill="#EED6A7",font=(FONT,9,"bold"))
        header.create_line(0,header_height-2,1600,header_height-2,
                           fill="#BC8A46",width=2)
        self.version_plate=header.create_image(0,0,image=plaque,anchor="ne")
        self.banner_version=header.create_text(0,0,text="",
            font=(FONT,11,"bold"),fill="#F8E0AE",anchor="e")
        def resize_header(event):
            header.coords(self.version_plate,event.width-9,8)
            header.coords(self.banner_version,event.width-22,28)
            header.itemconfigure(self.banner_version,
                                 text="v"+__import__("app").APP_VERSION)
        header.bind("<Configure>",resize_header)

        # Six working pages and one explicit service menu. All commands remain
        # reachable by keyboard and retain their existing callbacks.
        nav_shell=tk.Frame(outer,bg="#89633D",pady=1)
        nav_shell.pack(fill="x")
        nav=tk.Frame(nav_shell,bg=SIDEBAR)
        nav.pack(fill="x")
        buttons=[
            ("home",lambda:self.navigate("home")),
            ("translation",lambda:self.navigate("translation")),
            ("overlay",lambda:self.navigate("overlay")),
            ("knowledge",lambda:self.navigate("knowledge")),
            ("stats",lambda:self.navigate("stats")),
            ("settings",lambda:self.navigate("settings")),
        ]
        # At 125%/150% DPI use proportionally smaller typography so all
        # seven real navigation buttons fit without clipped labels.
        dpi_scale=float(self.root.tk.call("tk","scaling"))
        self._nav_font_size=9 if dpi_scale>=1.85 else 10 if dpi_scale>=1.6 else 11
        for index,(name,callback) in enumerate(buttons):
            nav.columnconfigure(index,weight=1,uniform="nav")
            photo=ui_photo(nav,"nav_"+name+".png") if name in {"home","knowledge","stats","settings"} else None
            button=ttk.Button(nav,text=nav_name(app,name),image=photo,compound="left",
                command=callback,style="PremiumNav.TButton",cursor="hand2")
            button.grid(row=0,column=index,sticky="nsew",padx=1,pady=1)
            self.nav_buttons[name]=button
        nav.columnconfigure(6,weight=1,uniform="nav")
        service=tk.Menu(nav,tearoff=False,bg="#2A241A",fg=TEXT,
                        activebackground="#9E540D",activeforeground=TEXT)
        service.add_command(label=nav_name(app,"updates"),
                            command=lambda:app.check_updates(manual=True))
        if FEATURED_SERVER.discord_url:
            service.add_command(label=nav_name(app,"discord"),
                                command=app._open_featured_server_discord)
        service.add_command(label=nav_name(app,"about"),command=app.show_about)
        self.service_menu=service
        caption={"ru":"Справка и сервис ▾","uk":"Довідка і сервіс ▾",
                 "en":"Help and service ▾"}.get(app.ui_language,"Help and service ▾")
        def show_service():
            service.tk_popup(service_button.winfo_rootx(),
                             service_button.winfo_rooty()+service_button.winfo_height())
        service_button=ttk.Button(nav,text=caption,style="PremiumNav.TButton",
                                  command=show_service,cursor="hand2")
        service_button.grid(row=0,column=6,sticky="nsew",padx=1,pady=1)
        self.service_button=service_button

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
        first.pack(fill="both",expand=True,padx=11,pady=5)
        self.footer_ready_dot=text(first,"●",color=MUTED,
                                   bg="#15130D",size=10)
        self.footer_ready_dot.pack(side="left")
        self.footer_f8=text(first,"F8",bg="#15130D",color=TEXT,bold=True,size=9)
        self.footer_f8.pack(side="left",padx=(5,15))
        self.footer_f9=text(first,"F9",bg="#15130D",color=TEXT,bold=True,size=9)
        self.footer_f9.pack(side="left",padx=(0,17))
        self.footer_engine=text(first,"",bg="#15130D",color=AMBER,bold=True,size=9)
        self.footer_engine.pack(side="left",padx=(6,19))
        self.footer_base=text(first,"",bg="#15130D",color=TEXT,size=9)
        self.footer_base.pack(side="left",padx=(5,18))
        self.footer_style=text(first,"",bg="#15130D",color=AMBER,size=9)
        self.footer_style.pack(side="left",padx=5)
        # status_var is the REAL latest application event, not decorative
        # fake latency. Any long message is clipped to its allocated width.
        self.footer_event=tk.Label(first,textvariable=app.status_var,bg="#15130D",
                 fg=TEXT,font=(FONT,9),anchor="e")
        self.footer_event.pack(side="right",fill="x",expand=True)
        self.navigate("home")

    def _home(self, page):
        # The illustrated chassis supplies only materials and scene artwork.
        # All input is handled by real controls in premium_home.PremiumHome.
        from premium_home import build_premium_home
        build_premium_home(self, page)

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
        self.footer_f8.configure(text="F8  "+("●" if app.enabled_var.get() else "○"),
                                 fg=GREEN if app.enabled_var.get() else MUTED)
        f9_on=bool(app.outgoing_chat.enabled_var.get())
        self.footer_f9.configure(text="F9  "+("●" if f9_on else "○"),
                                 fg=GREEN if f9_on else MUTED)


def build_dashboard(app):
    app._update_overlay_hotkey_status()
    app.dashboard=WWIIDashboard(app)
