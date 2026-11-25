"""Approved server-monitor command center, with live metal/Tk controls."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from dashboard_ui import (
    Dashboard, BG, CARD, SIDEBAR, TEXT, MUTED, AMBER, GREEN, BORDER,
    FONT, tr, text, card, action, check, label_combo, ui_photo,
)
from server_catalog import FEATURED_SERVER
from premium_material import MetalCanvas


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


class WWIIDashboard(Dashboard):
    """Horizontal navigation / original illustrated header / metal controls."""

    def _build(self):
        app=self.app
        request_dark_native_titlebar(self.root)
        compact_dpi=float(self.root.tk.call("tk","scaling"))>=1.6
        outer=tk.Frame(self.root,bg=BG)
        outer.pack(fill="both",expand=True)
        self.outer=outer
        # The brand is a separate, transparent, metallic raster asset built
        # from original artwork. Only the version and localized subtitle
        # are live text. The photographic hero contains no fake UI states.
        header_height=158 if self.root.winfo_screenheight()<=800 else 184
        header=tk.Canvas(outer,height=header_height,bg="#17130E",
                         highlightthickness=0,borderwidth=0)
        header.pack(fill="x")
        from PIL import Image,ImageTk
        from app import resource_path
        try:
            panorama=Image.open(resource_path("assets/ui_premium/header_panorama.jpg")).convert("RGB")
        except FileNotFoundError:
            panorama=Image.open(resource_path("assets/ui_premium/monitor_hero.png")).convert("RGB")
        brand_source=Image.open(resource_path("assets/ui_premium/monitor_logo.png")).convert("RGBA")
        self._header_photos={}
        hero_item=header.create_image(0,0,anchor="nw")
        logo_item=header.create_image(0,0,anchor="nw")
        tagline_item=header.create_text(0,0,text="Intelligent Gaming Companion",
                            anchor="w",fill="#F2DEB4",font=(FONT,10,"italic"))
        header.create_line(0,header_height-2,1600,header_height-2,
                           fill="#BC8A46",width=2)
        self.banner_version=header.create_text(0,0,text="",
            font=(FONT,9,"bold"),fill="#F8E0AE",anchor="e")
        def resize_header(event):
            width=max(1,event.width)
            # Cover the header with one original panoramic asset, without
            # baking live labels or hit targets into the image.
            # Exclude the portrait from the cover layer; the same soldier is
            # composited once at a scale that exposes helmet and backpack.
            backdrop=panorama.crop((min(610,panorama.width//3),0,panorama.width,panorama.height))
            scale=max(width/backdrop.width,header_height/backdrop.height)
            scaled=backdrop.resize((round(backdrop.width*scale),round(backdrop.height*scale)),Image.Resampling.LANCZOS)
            x=max(0,(scaled.width-width)//2)
            y=max(0,(scaled.height-header_height)//2)
            picture=scaled.crop((x,y,x+width,y+header_height)).convert("RGBA")
            # The base panorama must cover a very shallow window. Layer an
            # independently scaled portion of the same artwork so helmet,
            # shoulder and backpack all remain visible without distortion.
            portrait=panorama.crop((0,0,710,710))
            portrait_height=header_height+12
            portrait_width=round(portrait.width*portrait_height/portrait.height)
            portrait=portrait.resize((portrait_width,portrait_height),Image.Resampling.LANCZOS).convert("RGBA")
            fade=Image.new("L",(portrait_width,1))
            fade.putdata([min(255,max(0,int((portrait_width-i)*255/max(1,portrait_width*.46))))
                          for i in range(portrait_width)])
            portrait.putalpha(fade.resize(portrait.size))
            picture.alpha_composite(portrait,(0,0))
            self._header_photos["scene"]=ImageTk.PhotoImage(picture,master=header)
            header.itemconfigure(hero_item,image=self._header_photos["scene"])
            logo_width=min(510,round(width*.38),round(header_height*2.55))
            logo_height=round(brand_source.height*logo_width/brand_source.width)
            logo=brand_source.resize((logo_width,logo_height),Image.Resampling.LANCZOS)
            self._header_photos["logo"]=ImageTk.PhotoImage(logo,master=header)
            header.itemconfigure(logo_item,image=self._header_photos["logo"])
            header.coords(logo_item,round(width*.37),3)
            header.coords(tagline_item,round(width*.43),header_height-12)
            header.coords(self.banner_version,width-13,header_height-16)
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
            button.grid(row=0,column=index,sticky="nsew",padx=0,pady=0)
            if index:
                # A thin etched divider keeps the bar visually continuous.
                tk.Frame(nav,bg="#9F8259",width=1).grid(row=0,column=index,
                    sticky="ns",padx=0)
            self.nav_buttons[name]=button
        service=tk.Menu(nav,tearoff=False,bg="#2A241A",fg=TEXT,
                        activebackground="#9E540D",activeforeground=TEXT)
        service.add_command(label=nav_name(app,"updates"),
                            command=lambda:app.check_updates(manual=True))
        if FEATURED_SERVER.discord_url:
            service.add_command(label=nav_name(app,"discord"),
                                command=app._open_featured_server_discord)
        self.service_menu=service

        stack=tk.Frame(outer,bg=BG)
        stack.pack(fill="both",expand=True)
        self.stack=stack
        for name in ("home","servers","translation","overlay","knowledge","stats","settings","history"):
            page=tk.Frame(stack,bg=BG)
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
        for page_name in ("settings","translation","overlay","knowledge","stats"):
            row=tk.Frame(self.pages[page_name],bg="#29241D",height=38)
            row.pack(fill="x",side="top",before=self.pages[page_name].winfo_children()[0])
            if page_name=="settings":self.settings_expert_row=row
            for key in ("translation","overlay","knowledge","stats","settings"):
                tactical_action(row,nav_name(self.app,key),lambda destination=key:self.navigate(destination)).pack(
                    side="left",padx=5,pady=2)

    def navigate(self,name,*,add=False):
        if name not in self.pages:return False
        self.page=name
        self.pages[name].tkraise()
        if name=="stats":self.request_stats()
        if name=="servers" and add:self.root.after_idle(self.server_page.add)
        for key,button in self.nav_buttons.items():
            if button.instate(["disabled"]):continue
            active=key==name or (key=="settings" and name in ("translation","overlay","knowledge","stats"))
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
