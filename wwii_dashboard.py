"""Approved server-monitor command center, with live metal/Tk controls."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dashboard_ui import (
    Dashboard, BG, CARD, SIDEBAR, TEXT, MUTED, AMBER, GREEN, BORDER,
    FONT, tr, text, card, action, check, label_combo, ui_photo,
)
from server_catalog import FEATURED_SERVER
from premium_material import MetalCanvas, SteelFrame


def nav_name(app, name):
    choices = {
        "ru":{"home":"Главная","servers":"Серверы","history":"Логи / История","translation":"Перевод","overlay":"Оверлей",
              "knowledge":"База знаний","stats":"Статистика",
              "settings":"Настройки","updates":"Обновления","discord":"Discord","about":"О программе"},
        "uk":{"home":"Головна","servers":"Сервери","history":"Журнали / Історія","translation":"Переклад","overlay":"Оверлей",
              "knowledge":"База знань","stats":"Статистика",
              "settings":"Налаштування","updates":"Оновлення","discord":"Discord","about":"Про програму"},
        "en":{"home":"Home","servers":"Servers","history":"Logs / History","translation":"Translation","overlay":"Overlay",
              "knowledge":"Knowledge","stats":"Statistics",
              "settings":"Settings","updates":"Updates","discord":"Discord","about":"About"},
    }
    return choices.get(app.ui_language,choices["ru"])[name]


def tactical_action(parent, caption, command, *, primary=False, icon=None, style=None):
    """Real native button with amber metal states, not a painted hotspot."""
    button=ttk.Button(
        parent,text=caption,command=command,
        style=style or ("TacticalAccent.TButton" if primary else "Tactical.TButton"),
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


def request_dark_native_titlebar(root):
    """Ask DWM for dark title chrome while retaining native window controls."""
    import os
    if os.name != "nt":
        return
    def apply():
        try:
            import ctypes
            parent=ctypes.windll.user32.GetParent
            parent.argtypes=[ctypes.c_void_p]
            parent.restype=ctypes.c_void_p
            hwnd=parent(root.winfo_id()) or root.winfo_id()
            dwm=ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
            dwm.restype=ctypes.c_long
            value=ctypes.c_int(1)
            for attribute in (20, 19):
                if dwm(hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                    break
        except (AttributeError, OSError, RuntimeError):
            pass  # Older Windows keeps the normal system titlebar.
    root.after_idle(apply)


def home_banner_height(root):
    screen=root.winfo_screenheight()
    if screen>=1000:
        return 270
    if screen>=850:
        return 218
    return 145 if float(root.tk.call("tk","scaling"))>=1.95 else 185


class WWIIDashboard(Dashboard):
    """Horizontal navigation / original illustrated header / metal controls."""

    def _build(self):
        app=self.app
        request_dark_native_titlebar(self.root)
        compact_dpi=float(self.root.tk.call("tk","scaling"))>=1.6
        outer=SteelFrame(self.root,bg=BG)
        outer.pack(fill="both",expand=True)
        self.outer=outer
        # The brand is a separate, transparent, metallic raster asset built
        # from original artwork. Only the version and localized subtitle
        # are live text. The photographic hero contains no fake UI states.
        header_height=home_banner_height(self.root)
        header=tk.Canvas(outer,height=header_height,bg="#171A1D",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        self.header_widget=header
        from PIL import Image,ImageTk
        from app import resource_path
        from premium_banner import compose_banner
        # The live wordmark sits over one coherent painted city panorama.
        fallback="assets/ui_premium/monitor_hero.png"
        brand_source=Image.open(resource_path("assets/ui_premium/monitor_logo.png")).convert("RGBA")
        self._header_photos={}
        hero_item=header.create_image(0,0,anchor="nw")
        logo_item=header.create_image(0,0,anchor="nw")
        subtitle="\u2009".join("Intelligent Gaming Companion")
        tagline_shadow=header.create_text(0,0,text=subtitle,anchor="center",
            fill="#080B0B",font=(FONT,11,"italic"))
        tagline_item=header.create_text(0,0,text=subtitle,anchor="center",
            fill="#F2DFB6",font=(FONT,11,"italic"))
        self.banner_version=header.create_text(0,0,text="",
            font=(FONT,9,"bold"),fill="#F8E0AE",anchor="e")
        stars=[header.create_polygon(0,0,1,0,0,1,fill="#C8A576",
                       outline="#F1CE91",width=1) for _ in range(2)]
        logo_rule=header.create_line(0,0,0,0,fill="#DAAB62",width=1)
        def resize_header(event):
            width=max(1,event.width)
            height=max(120,event.height)
            picture=compose_banner(width,height)
            self._header_photos["scene"]=ImageTk.PhotoImage(picture,master=header)
            header.itemconfigure(hero_item,image=self._header_photos["scene"])
            logo_width=min(540,round(width*.38),round(height*2.7))
            logo_height=round(brand_source.height*logo_width/brand_source.width)
            logo=brand_source.resize((logo_width,logo_height),Image.Resampling.LANCZOS)
            self._header_photos["logo"]=ImageTk.PhotoImage(logo,master=header)
            header.itemconfigure(logo_item,image=self._header_photos["logo"])
            logo_x=round(width*.36)
            logo_y=max(-4,round((height-logo_height-25)/2))
            header.coords(logo_item,logo_x,logo_y)
            for star,offset in zip(stars,(.18,.82)):
                x=round(logo_x+logo_width*offset)
                y=logo_y+round(logo_height*.30)
                points=[]
                from math import cos, sin, pi
                for index in range(10):
                    angle=-pi/2+index*pi/5
                    radius=9 if index%2==0 else 4
                    points.extend((round(x+cos(angle)*radius),
                                   round(y+sin(angle)*radius)))
                header.coords(star,*points)
            rule_y=min(height-22,logo_y+logo_height-2)
            caption_y=min(height-13,rule_y+16)
            header.coords(logo_rule,logo_x+40,rule_y,
                          logo_x+logo_width-40,rule_y)
            header.coords(tagline_shadow,round(width*.55)+1,caption_y+1)
            header.coords(tagline_item,round(width*.55),caption_y)
            header.coords(self.banner_version,width-13,height-16)
            header.itemconfigure(self.banner_version,
                                 text="v"+__import__("app").APP_VERSION)
        header.bind("<Configure>",resize_header)

        # Five primary destinations mirror the approved concept. Expert
        # translation, overlay and knowledge tools remain directly reachable
        # through the Settings section.
        nav_shell=tk.Frame(outer,bg="#89633D",pady=1)
        nav_shell.pack(fill="x")
        nav=tk.Frame(nav_shell,bg=SIDEBAR)
        nav.pack(fill="x")
        buttons=[
            ("home",lambda:self.navigate("home")),
            ("servers",lambda:self.navigate("servers")),
            ("settings",lambda:self.navigate("settings")),
            ("history",lambda:self.navigate("history")),
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
            button.configure(takefocus=True)
            button.grid(row=0,column=index,sticky="nsew",padx=0,pady=0)
            if index:
                # Place the divider at the actual column boundary. Gridding
                # it in the same cell centered it over the tab's caption.
                tk.Frame(nav,bg="#756B5C",width=1).place(
                    relx=index/5,rely=.18,relheight=.64)
            self.nav_buttons[name]=button
        service=tk.Menu(nav,tearoff=False,bg="#2A241A",fg=TEXT,
                        activebackground="#9E540D",activeforeground=TEXT)
        service.add_command(label=nav_name(app,"updates"),
                            command=lambda:app.check_updates(manual=True))
        if FEATURED_SERVER.discord_url:
            service.add_command(label=nav_name(app,"discord"),
                                command=app._open_featured_server_discord)
        self.service_menu=service

        stack=SteelFrame(outer,bg=BG)
        stack.pack(fill="both",expand=True)
        self.stack=stack
        for name in ("home","servers","translation","overlay","knowledge","stats","settings","history"):
            page=SteelFrame(stack,bg=BG)
            page.place(relx=0,rely=0,relwidth=1,relheight=1)
            self.pages[name]=page
        self._home(self.pages["home"])
        from premium_server_page import ServerPage
        self.server_page=ServerPage(self,self.pages["servers"])
        self._translation(self.pages["translation"])
        self._overlay(self.pages["overlay"])
        self._knowledge(self.pages["knowledge"])
        self._stats(self.pages["stats"])
        self._settings(self.pages["settings"])
        from premium_history_page import build_history_page
        build_history_page(self,self.pages["history"])
        self._expert_links()
        caption={"ru":"Сервис ▾","uk":"Сервіс ▾","en":"Service ▾"}.get(app.ui_language,"Service ▾")
        def show_service():
            service.tk_popup(service_button.winfo_rootx(),
                             service_button.winfo_rooty()+service_button.winfo_height())
        service_button=ttk.Button(self.settings_expert_row,text=caption,
                                  style="Tactical.TButton",command=show_service)
        service_button.pack(side="right",padx=5,pady=2)
        self.service_button=service_button
        if app.overlay_editing:
            for key in ("overlay_edit_button","overlay_edit_button_alt"):
                widget=getattr(app,key,None)
                if widget:widget.configure(text=app.t("lock_overlay"))
        for page in self.pages.values():self._enable_page_wheel(page)
        footer=MetalCanvas(outer,height=46)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        first=tk.Frame(footer,bg="#15130D")
        first.pack(fill="both",expand=True,padx=16,pady=8)
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

    def _expert_links(self):
        self.expert_buttons={}
        for page_name in ("settings","translation","overlay","knowledge","stats"):
            row=SteelFrame(self.pages[page_name],bg=SIDEBAR,height=36)
            first_packed=next(child for child in self.pages[page_name].winfo_children()
                              if child.winfo_manager()=="pack")
            row.pack(fill="x",side="top",before=first_packed)
            if page_name=="settings":self.settings_expert_row=row
            buttons={}
            for key in ("translation","overlay","knowledge","stats","settings"):
                button=ttk.Button(row,text=nav_name(self.app,key),
                    image=ui_photo(row,"nav_"+key+".png"),compound="left",
                    command=lambda destination=key:self.navigate(destination),
                    style="PremiumNav.TButton",cursor="hand2",takefocus=True)
                button.pack(side="left",fill="x",expand=True,padx=0,pady=1)
                buttons[key]=button
            self.expert_buttons[page_name]=buttons

    def navigate(self,name,*,add=False):
        if name not in self.pages:return False
        self.page=name
        self.pages[name].tkraise()
        self.header_widget.configure(height=home_banner_height(self.root) if name=="home" else 155)
        if name=="stats":self.request_stats()
        if name=="servers" and add:self.root.after_idle(self.server_page.add)
        for key,button in self.nav_buttons.items():
            if button.instate(["disabled"]):continue
            active=key==name or (key=="settings" and name in ("translation","overlay","knowledge","stats"))
            button.configure(style="PremiumNavActive.TButton" if active
                             else "PremiumNav.TButton")
        for buttons in getattr(self,"expert_buttons",{}).values():
            for key,button in buttons.items():
                button.configure(style="PremiumNavActive.TButton" if key==name
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
