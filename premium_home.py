"""Live command center with two translation bays and a CoD2 server monitor."""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from dashboard_ui import BG, CARD, CARD_ALT, TEXT, MUTED, AMBER, GREEN, FONT
from server_monitor import color_runs, normalized_name
from premium_material import MetalCanvas, CanvasKeycap, SteelFrame
from premium_roster import PlayerRoster


def local(app, ru, uk, en):
    return {"ru":ru,"uk":uk,"en":en}.get(app.ui_language,en)

localized=local  # Existing expert translation page imports this helper.


def txt(parent, value, size=10, color=TEXT, bold=False, bg=None):
    return tk.Label(parent,text=value,font=(FONT,size,"bold" if bold else "normal"),
                    bg=bg or parent.cget("bg"),fg=color,anchor="w")


class CanvasText:
    """Keep the live status text API while painting on the card's artwork."""

    def __init__(self, canvas, item):
        self.canvas, self.item = canvas, item

    def configure(self, **kwargs):
        if "fg" in kwargs:
            kwargs["fill"]=kwargs.pop("fg")
        self.canvas.itemconfigure(self.item, **kwargs)

    def cget(self, name):
        return self.canvas.itemcget(self.item, name)


class PremiumHome:
    def __init__(self,dashboard,page):
        self.dashboard,self.app,self.page=dashboard,dashboard.app,page
        self.selected=None
        self.sort_key="favorite"
        self.reverse=False
        self.dpi=float(self.app.root.tk.call("tk","scaling"))
        self.compact=self.app.root.winfo_height()<=760 or self.app.root.winfo_screenheight()<=800
        self.large_dpi=self.dpi>=1.95
        self.photos={}
        from app import resource_path
        self.scene=Image.open(resource_path("assets/ui_premium/monitor_hero.png")).convert("RGB")
        self._build()

    def _build(self):
        self.canvas=tk.Canvas(self.page,bg=BG,highlightthickness=0)
        bar=ttk.Scrollbar(self.page,orient="vertical",style="Premium.Vertical.TScrollbar",command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(fill="both",expand=True)
        self.content=SteelFrame(self.canvas,bg=BG)
        item=self.canvas.create_window((0,0),window=self.content,anchor="nw")
        self.dashboard.home_canvas=self.canvas
        self.dashboard.home_content=self.content
        self.dashboard.home_scrollbar=bar
        self._measure_timer=None
        self._last_measure=None
        def measure(_event=None):
            if self._measure_timer is not None:self.canvas.after_cancel(self._measure_timer)
            self._measure_timer=self.canvas.after(60,apply_measure)
        def apply_measure():
            self._measure_timer=None
            width,height=self.canvas.winfo_width(),self.canvas.winfo_height()
            self.canvas.itemconfigure(item,width=width)
            # Fit to the real client viewport. Scrollbars float above the
            # content and cannot change its width or feed Configure cycles.
            rail_height=100 if self.compact else 112
            if int(self.rail.cget("height"))!=rail_height:self.rail.configure(height=rail_height)
            card_height=max(145,min(190,(height-rail_height-43)//2))
            for card in getattr(self,"_cards",()):
                if int(card.cget("height"))!=card_height:card.configure(height=card_height)
            required=self.content.winfo_reqheight()
            geometry=(width,height,required)
            if geometry==self._last_measure:return
            self._last_measure=geometry
            self.canvas.configure(scrollregion=(0,0,width,required))
            if required>height+2:
                bar.place(relx=1.0,rely=0,relheight=1.0,anchor="ne",width=11)
            else:bar.place_forget()
        self.content.bind("<Configure>",measure)
        self.canvas.bind("<Configure>",measure)
        columns=SteelFrame(self.content,bg=BG)
        columns.pack(fill="both",expand=True,padx=14,
                     pady=(4,2) if self.compact else (8,5))
        columns.columnconfigure(0,weight=44,uniform="command",minsize=380)
        columns.columnconfigure(1,weight=56,uniform="command",minsize=520)
        left=SteelFrame(columns,bg=BG)
        right=SteelFrame(columns,bg=BG)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._translator(left,"f8")
        self._translator(left,"f9")
        self._monitor(right)
        self._rail()
        self.render()

    def _translator(self,parent,kind):
        a=self.app
        from wwii_dashboard import tactical_switch
        height=((162 if self.large_dpi else 149) if self.compact else
                265 if self.app.root.winfo_screenheight()>=1000 else
                202 if self.app.root.winfo_screenheight()>=850 else
                244 if self.large_dpi else 190)
        scene=("assets/ui_premium/translation_card_source.jpg" if kind=="f8"
               else "assets/ui_premium/tank_card.png")
        card=MetalCanvas(parent,scene=scene,height=height)
        if not hasattr(self,"_cards"):self._cards=[]
        self._cards.append(card)
        card.pack(fill="both",expand=True,
                  pady=(0,7 if self.compact else 2 if self.large_dpi else 5))
        card.pack_propagate(False)
        key=CanvasKeycap(card,kind.upper(),lambda:switch.invoke(),size=100 if self.compact else 116)
        setattr(self,kind+"_key",key)
        title=local(a,"Входящий перевод","Вхідний переклад","Incoming translation") if kind=="f8" else local(a,"Исходящий перевод","Вихідний переклад","Outgoing translation")
        note=local(a,"Перевод чата игроков","Переклад чату гравців","Translate player chat") if kind=="f8" else local(a,"Перевод ваших сообщений","Переклад ваших повідомлень","Translate your messages")
        # Draw captions on the artwork itself. Tk frames are always opaque and
        # used to obscure almost all of both illustrated cards on Windows.
        title_shadow=card.create_text(0,0,text=title,anchor="nw",fill="#111211",
                    font=(FONT,12 if self.large_dpi else 14 if self.compact else 17,"bold"))
        title_id=card.create_text(0,0,text=title,anchor="nw",fill="#FFF1D4",
                    font=(FONT,12 if self.large_dpi else 14 if self.compact else 17,"bold"))
        note_id=card.create_text(0,0,text=note,anchor="nw",fill="#E3C8A3",font=(FONT,10))
        detail_id=card.create_text(0,0,text="",anchor="nw",fill="#F1D5A2",font=(FONT,10))
        setattr(self,kind+"_detail",CanvasText(card,detail_id))
        var,callback=(a.enabled_var,a.toggle_enabled) if kind=="f8" else (a.outgoing_chat.enabled_var,a._outgoing_enabled_changed)
        switch=tactical_switch(card,local(a,"Вкл","Увімк","On"),var,callback)
        switch_id=card.create_window(0,0,window=switch,anchor="nw")
        setattr(self,kind+"_switch",switch)
        if kind=="f8":
            from app import TARGET_LANGUAGES
            values=list(TARGET_LANGUAGES)
            custom=a._custom_language_label()
            if custom:values.append(custom)
            combo=ttk.Combobox(card,textvariable=a.target_name_var,values=values,state="readonly",width=14)
            combo.bind("<<ComboboxSelected>>",lambda _e:a._persist_settings())
            a.language_combo=combo
        else:
            from outgoing_chat import LANGUAGES
            combo=ttk.Combobox(card,textvariable=a.outgoing_chat.target_name_var,
                               values=list(LANGUAGES),state="readonly",width=14)
            combo.bind("<<ComboboxSelected>>",a.outgoing_chat._languages_changed)
        combo_id=card.create_window(0,0,window=combo,anchor="nw")
        def position(event):
            left=148 if self.compact or self.large_dpi else 165
            shift=max(0,(event.height-(149 if self.compact else 190))//2)
            card.coords(title_id,left,(20 if self.compact else 24)+shift)
            card.coords(title_shadow,left+2,(22 if self.compact else 26)+shift)
            for size in range(12 if self.large_dpi else 14 if self.compact else 17,8,-1):
                card.itemconfigure(title_id,font=(FONT,size,"bold"))
                card.itemconfigure(title_shadow,font=(FONT,size,"bold"))
                if card.bbox(title_id)[2] <= event.width-19:
                    break
            card.coords(note_id,left,(47 if self.compact else 58)+shift)
            controls_y=(72 if self.compact else 92)+shift
            card.coords(switch_id,left,controls_y)
            card.coords(combo_id,left+94,controls_y)
            # Show the full translation route below controls; no opaque strip.
            card.coords(detail_id,left,(108 if self.compact else 135)+shift)
            combo.configure(width=12 if event.width<530 else 17)
        card.bind("<Configure>",position,add="+")
        # Full translation controls live in the Settings/Translation section.

    def _monitor(self,parent):
        a=self.app
        from wwii_dashboard import tactical_action
        border=MetalCanvas(parent)
        border.pack(fill="both",expand=True)
        box=tk.Frame(border,bg=CARD,height=(330 if self.large_dpi else 330) if self.compact
                     else 545 if self.app.root.winfo_screenheight()>=1000 else
                     423 if self.app.root.winfo_screenheight()>=850 else
                     492 if self.large_dpi else 390)
        box.pack(fill="both",expand=True,padx=10,pady=10)
        box.pack_propagate(False)
        head=tk.Frame(box,bg=CARD,height=40)
        head.pack(fill="x")
        head.pack_propagate(False)
        from dashboard_ui import ui_photo
        tk.Label(head,image=ui_photo(head,"premium_radio.png"),bg=CARD).pack(side="left",padx=(9,3))
        txt(head,local(a,"Мониторинг серверов","Моніторинг серверів","Server Monitor"),13 if self.large_dpi else 16,bold=True,bg=CARD).pack(side="left",padx=4)
        self.friends_badge=txt(head,"",9 if self.large_dpi else 10,GREEN,bold=True)
        self.friends_badge.pack(side="right",padx=5 if self.large_dpi else 12)
        tk.Label(head,image=ui_photo(head,"quick_friends.png"),bg=CARD).pack(side="right",padx=(0,3))
        style=ttk.Style()
        # The clam theme's default field element draws a light system rim.
        # Keep its real keyboard-aware Treeview but remove that field border.
        style.layout("Monitor.Treeview",[("Treeview.padding",{"sticky":"nsew",
            "children":[("Treeview.treearea",{"sticky":"nsew"})]})])
        style.configure("Monitor.Treeview",background="#1C2022",foreground=TEXT,
                        fieldbackground="#1C2022",rowheight=29,font=(FONT,9 if self.large_dpi else 10),borderwidth=0,
                        relief="flat")
        style.configure("Monitor.Treeview.Heading",background="#343A3C",foreground="#F4D49A",
                        bordercolor="#665C4B",lightcolor="#44494A",darkcolor="#202325",
                        font=(FONT,8 if self.large_dpi else 9,"bold"),padding=(3,5))
        style.map("Monitor.Treeview.Heading",background=[("active","#565148")])
        if "Monitor.selection" not in style.element_names():
            style.element_create("Monitor.selection", "image",
                                 ui_photo(head,"premium_selection_clear.png"),
                                 ("selected",ui_photo(head,"premium_selection.png")),
                                 border=(7,4,7,4),sticky="nsew")
        style.layout("Monitor.Treeview.Cell",[("Monitor.selection",{"sticky":"nsew",
            "children":[("Treeitem.text",{"sticky":"nsew"})]})])
        # Explicitly replace clam's blue selection base; the translucent
        # artwork above it then reads as bronze on every ttk platform.
        style.map("Monitor.Treeview",background=[("selected","#594832")],
                  foreground=[("selected","#FFF0CF")])
        style.configure("Monitor.Treeview.Heading",relief="flat",borderwidth=0)
        area=tk.Frame(box,bg=BG)
        area.pack(fill="x",padx=8,pady=(1,2))
        columns=("star","name","map","players","ping","status")
        self.tree=ttk.Treeview(area,columns=columns,show="headings",height=2 if self.compact else 3,
                               style="Monitor.Treeview",selectmode="browse")
        names=("★",local(a,"Сервер","Сервер","Server"),local(a,"Карта","Мапа","Map"),
               local(a,"Игроки","Гравці","Players"),local(a,"Пинг","Пінг","Ping"),
               local(a,"Статус","Стан","Status"))
        widths=(30,140,110,85,90,115) if self.dpi>=1.6 else (30,140,85,75,74,95)
        for key,title,width in zip(columns,names,widths):
            self.tree.heading(key,text=title,command=lambda k=key:self._sort(k))
            self.tree.column(key,width=width,minwidth=width,stretch=key=="name",
                             anchor="w" if key=="name" else "center")
        self.tree.tag_configure("offline",foreground="#AAA69F")
        self.tree.tag_configure("even",background="#22282A")
        self.tree.tag_configure("odd",background="#1C2123")
        self.tree.pack(side="left",fill="both",expand=True)
        sb=ttk.Scrollbar(area,orient="vertical",style="Premium.Vertical.TScrollbar",command=self.tree.yview)
        sb.pack(side="right",fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>",lambda _e:self._select())
        self.tree.bind("<Double-1>",lambda _e:self.connect_selected())
        self.tree.bind("<Motion>",self._show_truncated_cell)
        self.tree.bind("<Leave>",lambda _e:self._hide_tip())
        heading=tk.Frame(box,bg=CARD_ALT,height=29)
        heading.pack(fill="x",padx=8)
        self.player_title=txt(heading,"",10,AMBER,bold=True)
        self.player_title.pack(side="left",padx=7)
        self.last_update=txt(heading,"",9,MUTED)
        self.last_update.pack(side="right",padx=7)
        self.players=PlayerRoster(box,labels=(local(a,"Никнейм","Нікнейм","Nickname"),
                    local(a,"Счёт","Рахунок","Score"),local(a,"Пинг","Пінг","Ping")),
                    rows=3 if self.compact and self.dpi>=1.65 else 5 if self.compact else 4,
                    zero_hint=local(a,"Сервер сообщил 0 ms; задержка неизвестна",
                                    "Сервер повідомив 0 ms; затримка невідома",
                                    "Server reported 0 ms; actual ping unknown"))
        self.players.pack(fill="both",expand=True,padx=8,pady=(0,4))
        actions=tk.Frame(box,bg=CARD)
        actions.pack(fill="x",padx=7,pady=(0,3))
        for title,command,primary,icon in (
            (local(a,"Добавить сервер","Додати сервер","Add server"),
             lambda:self.dashboard.navigate("servers",add=True),False,"add"),
            (local(a,"Обновить","Оновити","Refresh"),a.monitor.refresh,False,"updates"),
            (local(a,"Подключиться","Підключитися","Connect"),self.connect_selected,True,"test"),
        ):
            tactical_action(actions,title,command,primary=primary,
                            icon=None if self.large_dpi and self.app.root.winfo_screenwidth()<=1366 else icon).pack(
                            side="left",fill="x",expand=True,padx=2)

    def _rail(self):
        a=self.app
        from wwii_dashboard import tactical_action, tactical_switch
        from dashboard_ui import ui_photo
        rail=MetalCanvas(self.content,height=110 if self.compact else
                         128 if a.root.winfo_screenheight()>=1000 else 112)
        self.rail=rail
        rail.pack(fill="x",padx=14,pady=(0,6))
        # One textured surface carries the three sections. Only the actual
        # controls are Tk child windows; captions and separators do not hide it.
        overlay_icon=rail.create_image(0,0,image=ui_photo(rail,"premium_overlay_rail.png"),anchor="center")
        engine_icon=rail.create_image(0,0,image=ui_photo(rail,"premium_chip_rail.png"),anchor="center")
        rail.create_text(0,0,text=local(a,"Оверлей","Оверлей","Overlay"),anchor="w",
                         fill=TEXT,font=(FONT,12,"bold"),tags="overlay_title")
        rail.create_text(0,0,text=local(a,"Перевод поверх игры","Переклад поверх гри",
                         "Translation over the game"),anchor="w",
                         fill=MUTED,font=(FONT,9),tags="overlay_note")
        rail.create_text(0,0,text="Smart Engine",anchor="w",
                         fill=TEXT,font=(FONT,12,"bold"),tags="engine_title")
        rail.create_text(0,0,text=local(a,"Умный игровой перевод","Розумний ігровий переклад",
                         "Intelligent game translation"),anchor="w",
                         fill=MUTED,font=(FONT,9),tags="engine_note")
        rail.create_oval(0,0,0,0,outline="#4A7953",fill="",width=2,tags="status_icon")
        rail.create_text(0,0,text="✓",fill=GREEN,font=(FONT,19,"bold"),tags="status_mark")
        self.status_surface=rail
        rail.create_text(0,0,text=local(a,"Состояние системы","Стан системи","System status"),
                         anchor="w",fill=TEXT,font=(FONT,12,"bold"),tags="status_title")
        separators=[rail.create_line(0,0,0,0,fill="#86643B",width=1) for _ in range(2)]
        self.overlay_var=tk.BooleanVar(value=a.overlay_hotkey_visible)
        def toggle_overlay():
            if self.overlay_var.get()!=a.overlay_hotkey_visible:
                a.toggle_overlay_hotkey_visibility()
        self.overlay_switch=tactical_switch(rail,"",self.overlay_var,toggle_overlay)
        overlay_switch=rail.create_window(0,0,window=self.overlay_switch,anchor="nw")
        a.overlay_edit_button=tactical_action(
            rail,local(a,"Место","Місце","Position"),a.toggle_overlay_edit,
            style="TacticalRail.TButton")
        overlay_edit=rail.create_window(0,0,window=a.overlay_edit_button,anchor="nw")
        config=tactical_action(rail,local(a,"Настроить →","Налаштувати →","Configure →"),
                               lambda:self.dashboard.navigate("overlay"),style="TacticalRail.TButton")
        overlay_config=rail.create_window(0,0,window=config,anchor="nw")
        engine_switch=tactical_switch(rail,"",a.smart_engine_var,a._persist_settings)
        engine_control=rail.create_window(0,0,window=engine_switch,anchor="nw")
        self.dashboard.engine_engine_bullet=CanvasText(rail,rail.create_text(
            0,0,text="●",anchor="w",fill=GREEN,font=(FONT,10)))
        self.dashboard.engine_engine_label=CanvasText(rail,rail.create_text(
            0,0,text="",anchor="w",fill=TEXT,font=(FONT,10)))
        self.dashboard.engine_pack_label=CanvasText(rail,rail.create_text(
            0,0,text="",anchor="w",fill=MUTED,font=(FONT,9)))
        self.system_status=CanvasText(rail,rail.create_text(
            0,0,text="",anchor="w",fill=GREEN,font=(FONT,10)))
        self.game_status=CanvasText(rail,rail.create_text(
            0,0,text="",anchor="w",fill=MUTED,font=(FONT,9)))
        def layout(event):
            width=event.width
            third=width/3
            dy=max(0,(event.height-112)//2)
            for index,item in enumerate(separators,1):
                x=round(third*index)
                rail.coords(item,x,13,x,event.height-13)
            rail.coords(overlay_icon,43,37+dy)
            rail.coords("overlay_title",72,31+dy)
            rail.coords("overlay_note",70,51+dy)
            rail.coords(overlay_switch,round(third-88),25+dy)
            action_y=64 if a.root.winfo_screenheight()<1000 else 70
            rail.coords(overlay_edit,35,action_y+dy)
            rail.coords(overlay_config,151,action_y+dy)
            rail.coords(engine_icon,round(third+43),37+dy)
            rail.coords("engine_title",round(third+72),31+dy)
            rail.coords("engine_note",round(third+70),51+dy)
            rail.coords(engine_control,round(third*2-88),25+dy)
            rail.coords(self.dashboard.engine_engine_bullet.item,round(third+39),
                        (68 if self.compact else 76)+dy)
            rail.coords(self.dashboard.engine_engine_label.item,round(third+58),
                        (68 if self.compact else 76)+dy)
            rail.coords(self.dashboard.engine_pack_label.item,
                        round(third+176 if self.large_dpi else third+145),
                        (68 if self.compact else 76)+dy)
            rail.coords("status_icon",round(third*2+28),19+dy,
                        round(third*2+63),54+dy)
            rail.coords("status_mark",round(third*2+45),36+dy)
            rail.coords("status_title",round(third*2+75),31+dy)
            rail.coords(self.system_status.item,round(third*2+70),
                        (54 if self.compact else 62)+dy)
            rail.coords(self.game_status.item,round(third*2+70),
                        (74 if self.compact else 82)+dy)
        rail.bind("<Configure>",layout,add="+")

    def _hide_tip(self):
        tip=getattr(self,"_tip",None)
        if tip is not None:
            tip.destroy()
            self._tip=None
        self._tip_value=None

    def _show_truncated_cell(self,event):
        column=self.tree.identify_column(event.x)
        row=self.tree.identify_row(event.y)
        if not row or column not in ("#2","#3"):
            self._hide_tip()
            return
        value=str(self.tree.set(row,"name" if column=="#2" else "map"))
        bbox=self.tree.bbox(row,column)
        if not bbox:
            self._hide_tip()
            return
        from tkinter import font as tkfont
        if not hasattr(self,"_cell_font"):
            self._cell_font=tkfont.Font(font=(FONT,10))
        if self._cell_font.measure(value)<=bbox[2]-12:
            self._hide_tip()
            return
        identity=(row,column,value)
        if identity==getattr(self,"_tip_value",None):return
        self._hide_tip()
        tip=tk.Toplevel(self.tree)
        tip.withdraw()
        tip.overrideredirect(True)
        tk.Label(tip,text=value,bg="#29221A",fg="#FFF1D4",
                 font=(FONT,10),padx=9,pady=5,
                 highlightthickness=1,highlightbackground="#A9783C").pack()
        tip.geometry(f"+{event.x_root+12}+{event.y_root+14}")
        tip.deiconify()
        self._tip,self._tip_value=tip,identity

    def _rows(self):
        rows=[]
        for s in self.app.monitor_settings["servers"]:
            snap=self.app.monitor.snapshots.get(s.address)
            state=snap.state if snap else "waiting"
            status=("● "+local(self.app,"Онлайн","Онлайн","Online")) if state=="online" else (
                "◐ "+local(self.app,"Частично","Частково","Partial") if state=="limited" else
                "○ "+local(self.app,"Нет ответа","Немає відповіді","No response") if state=="offline" else "…")
            values=("★" if s.favorite else "☆",s.label or (snap.name if snap else "") or s.address,
                    snap.map_name if snap else "—",
                    f"{snap.clients if snap.clients is not None else '—'}/{snap.max_clients if snap.max_clients is not None else '—'}" if snap else "—",
                    f"{snap.ping_ms} ms" if snap and snap.ping_ms is not None else "—",status)
            rows.append((s.address,values,state))
        def sort(row):
            address,values,_=row
            if self.sort_key=="favorite":return (values[0]!="★",values[1].casefold())
            index=("star","name","map","players","ping","status").index(self.sort_key)
            snap=self.app.monitor.snapshots.get(address)
            if self.sort_key=="players":return snap.clients if snap and snap.clients is not None else -1
            if self.sort_key=="ping":return snap.ping_ms if snap and snap.ping_ms is not None else 99999
            return str(values[index]).casefold()
        return sorted(rows,key=sort,reverse=self.reverse)

    def _sort(self,key):
        self.reverse=not self.reverse if key==self.sort_key else False
        self.sort_key=key
        self.render()

    def _select(self):
        chosen=self.tree.selection()
        if chosen:self.selected=chosen[0]
        self._render_players()

    def render(self):
        if hasattr(self,"overlay_var"):
            self.overlay_var.set(self.app.overlay_hotkey_visible)
        previous=self.selected
        position=self.tree.yview()[0]
        rows=self._rows()
        expected={address for address,_values,_state in rows}
        for item in self.tree.get_children():
            if item not in expected:self.tree.delete(item)
        for index,(address,values,state) in enumerate(rows):
            tags=("even" if index%2==0 else "odd",)
            if state not in ("online","limited"):
                tags+=("offline",)
            if self.tree.exists(address):
                if tuple(str(v) for v in self.tree.item(address,"values"))!=tuple(str(v) for v in values) or self.tree.item(address,"tags")!=tags:
                    self.tree.item(address,values=values,tags=tags)
                if self.tree.index(address)!=index:self.tree.move(address,"",index)
            else:self.tree.insert("",index,iid=address,values=values,tags=tags)
        if previous not in self.tree.get_children():
            previous=self.tree.get_children()[0] if self.tree.get_children() else None
        if previous:self.tree.selection_set(previous);self.selected=previous
        self.tree.yview_moveto(position)
        self._render_players()
        names={normalized_name(f) for f in self.app.monitor_settings["friends"]}
        online={(normalized_name(p.name),s.address) for s in self.app.monitor_settings["servers"]
                for snap in [self.app.monitor.snapshots.get(s.address)]
                if snap and snap.state=="online" for p in snap.players
                if normalized_name(p.name) in names}
        self.friends_badge.configure(text=(local(self.app,"Друзья: ","Друзі: ","Friends: ") if self.large_dpi else
            local(self.app,"Друзья в игре: ","Друзі у грі: ","Friends online: "))+str(len(online)))
        enabled=bool(self.app.enabled_var.get() or self.app.outgoing_chat.enabled_var.get())
        log=self.app.current_log_path()
        log_available=bool(log and log.is_file())
        game_detected=False
        if os.name=="nt":
            from app import find_cod2_window
            game_detected=bool(find_cod2_window())
        ready=enabled and log_available and game_detected
        if not enabled:
            status=local(self.app,"Перевод выключен","Переклад вимкнено","Translation off")
        elif not log_available:
            status=(local(self.app,"Игровой журнал не найден","Ігровий журнал не знайдено",
                          "Game log missing") if self.large_dpi else
                    local(self.app,"Движок готов · журнал не найден",
                          "Рушій готовий · журнал не знайдено",
                          "Engine ready · game log missing"))
        elif not game_detected and os.name=="nt":
            status=local(self.app,"Движок готов · игра не обнаружена",
                         "Рушій готовий · гру не виявлено", "Engine ready · game not detected")
        else:
            status=(local(self.app,"Перевод активен","Переклад активний",
                          "Translation active") if self.large_dpi else
                    local(self.app,"Журнал доступен · перевод активен",
                          "Журнал доступний · переклад активний",
                          "Game log found · translation active"))
        status_color=GREEN if ready else AMBER if enabled else MUTED
        self.system_status.configure(text=status, fg=status_color)
        self.status_surface.itemconfigure("status_icon",
            outline=status_color)
        self.status_surface.itemconfigure("status_mark",text="✓" if ready else "!" if enabled else "—",fill=status_color)
        if os.name=="nt":
            game_label=(local(self.app,"Окно CoD2 обнаружено","Вікно CoD2 виявлено","CoD2 window detected")
                        if game_detected else
                        local(self.app,"Окно CoD2 не обнаружено","Вікно CoD2 не виявлено","CoD2 window not detected"))
            self.game_status.configure(text=game_label,fg=GREEN if game_detected else MUTED)
        else:
            self.game_status.configure(text=local(self.app,"Проверка игры — в Windows",
                "Перевірка гри — у Windows","Game detection — Windows only"),fg=MUTED)
        self.f8_detail.configure(text="Auto → "+self.app.target_name_var.get())
        self.f9_detail.configure(text=self.app.outgoing_chat.route_var.get())

    def _render_players(self):
        a=self.app
        snap=a.monitor.snapshots.get(self.selected) if self.selected else None
        title=local(a,"Игроки на сервере","Гравці на сервері","Players")
        if snap and snap.state=="online":title+=f": {len(snap.players)}"
        if snap and snap.state=="limited":title+=" · "+local(a,"список недоступен","список недоступний","list unavailable")
        self.player_title.configure(text=title)
        self.last_update.configure(text=snap.last_success.astimezone().strftime("%H:%M:%S") if snap and snap.last_success else "—")
        empty=local(a,"Ожидание ответа…" if not snap else "Нет ответа; старые данные не считаются текущими.",
                    "Очікування відповіді…" if not snap else "Немає відповіді; старі дані застаріли.",
                    "Waiting for response…" if not snap else "No response; previous data is stale.")
        if snap and snap.state=="online":
            empty=local(a,"Игроков сейчас нет.","Гравців зараз немає.","No players currently.")
        self.players.render(sorted(snap.players,key=lambda p:(-(p.score or 0),p.name.casefold()))
                            if snap and snap.state=="online" else (),
                            friends=a.monitor_settings["friends"],empty=empty)

    def update_snapshot(self,snapshot):
        if self.page.winfo_exists():self.render()

    def connect_selected(self):
        if not self.selected:return
        server=next((s for s in self.app.monitor_settings["servers"] if s.address==self.selected),None)
        if server:self.app._launch_server(server.address,server.label)


def build_premium_home(dashboard,page):
    dashboard.premium_home=PremiumHome(dashboard,page)
