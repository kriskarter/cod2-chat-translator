"""Live command center with two translation bays and a CoD2 server monitor."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from dashboard_ui import BG, CARD, TEXT, MUTED, AMBER, GREEN, FONT
from server_monitor import color_runs, normalized_name
from premium_material import MetalCanvas, Keycap
from premium_roster import PlayerRoster


def local(app, ru, uk, en):
    return {"ru":ru,"uk":uk,"en":en}.get(app.ui_language,en)

localized=local  # Existing expert translation page imports this helper.


def txt(parent, value, size=10, color=TEXT, bold=False, bg=None):
    return tk.Label(parent,text=value,font=(FONT,size,"bold" if bold else "normal"),
                    bg=bg or parent.cget("bg"),fg=color,anchor="w")


class PremiumHome:
    def __init__(self,dashboard,page):
        self.dashboard,self.app,self.page=dashboard,dashboard.app,page
        self.selected=None
        self.sort_key="favorite"
        self.reverse=False
        self.dpi=float(self.app.root.tk.call("tk","scaling"))
        self.compact=self.app.root.winfo_screenheight()<=800 and self.dpi<1.85
        self.large_dpi=self.dpi>=1.95
        self.photos={}
        from app import resource_path
        self.scene=Image.open(resource_path("assets/ui_premium/monitor_hero.png")).convert("RGB")
        self._build()

    def _build(self):
        self.canvas=tk.Canvas(self.page,bg=BG,highlightthickness=0)
        bar=ttk.Scrollbar(self.page,orient="vertical",command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left",fill="both",expand=True)
        self.content=tk.Frame(self.canvas,bg=BG)
        item=self.canvas.create_window((0,0),window=self.content,anchor="nw")
        self.dashboard.home_canvas=self.canvas
        self.dashboard.home_content=self.content
        self.dashboard.home_scrollbar=bar
        def measure(_event=None):
            needed=self.content.winfo_reqheight()>self.canvas.winfo_height()+2
            self.canvas.configure(scrollregion=(0,0,self.canvas.winfo_width(),self.content.winfo_reqheight()))
            if needed and not bar.winfo_manager():bar.pack(side="right",fill="y")
            elif not needed and bar.winfo_manager():bar.pack_forget()
        self.content.bind("<Configure>",measure)
        self.canvas.bind("<Configure>",lambda e:(self.canvas.itemconfigure(item,width=e.width),measure()))
        columns=tk.Frame(self.content,bg=BG)
        columns.pack(fill="both",expand=True,padx=14,
                     pady=(4,2) if self.compact else (8,5))
        columns.columnconfigure(0,weight=44,uniform="command",minsize=380)
        columns.columnconfigure(1,weight=56,uniform="command",minsize=520)
        left=tk.Frame(columns,bg=BG)
        right=tk.Frame(columns,bg=BG)
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
        height=149 if self.compact else 244 if self.large_dpi else 190
        card=MetalCanvas(parent,scene="assets/ui_premium/translation_card_source.jpg",height=height)
        card.pack(fill="x",pady=(0,7 if self.compact else 2 if self.large_dpi else 5))
        card.pack_propagate(False)
        key=Keycap(card,kind.upper(),lambda:switch.invoke(),size=100 if self.compact else 116)
        key.place(x=23,rely=.5,anchor="w")
        setattr(self,kind+"_key",key)
        foreground=tk.Frame(card,bg="#26201A")
        foreground.place(relx=.27,relwidth=.60,y=19 if self.compact else 34,
                         height=112 if self.compact else 184 if self.large_dpi else 143)
        title=local(a,"Входящий перевод","Вхідний переклад","Incoming translation") if kind=="f8" else local(a,"Исходящий перевод","Вихідний переклад","Outgoing translation")
        txt(foreground,title,14 if self.compact else 17,bold=True,bg="#26201A").pack(fill="x",padx=6,pady=(1 if self.compact else 5,0))
        note=local(a,"Перевод чата игроков","Переклад чату гравців","Translate player chat") if kind=="f8" else local(a,"Перевод ваших сообщений","Переклад ваших повідомлень","Translate your messages")
        txt(foreground,note,10,MUTED,bg="#26201A").pack(fill="x",padx=6)
        row=tk.Frame(foreground,bg="#26201A")
        row.pack(fill="x",padx=5,pady=(5 if self.compact else 12,1))
        var,callback=(a.enabled_var,a.toggle_enabled) if kind=="f8" else (a.outgoing_chat.enabled_var,a._outgoing_enabled_changed)
        switch=tactical_switch(row,local(a,"Вкл","Увімк","On"),var,callback)
        switch.pack(side="left")
        setattr(self,kind+"_switch",switch)
        if kind=="f8":
            from app import TARGET_LANGUAGES
            values=list(TARGET_LANGUAGES)
            custom=a._custom_language_label()
            if custom:values.append(custom)
            combo=ttk.Combobox(row,textvariable=a.target_name_var,values=values,state="readonly",width=14)
            combo.bind("<<ComboboxSelected>>",lambda _e:a._persist_settings())
            a.language_combo=combo
        else:
            from outgoing_chat import LANGUAGES
            combo=ttk.Combobox(row,textvariable=a.outgoing_chat.target_name_var,
                               values=list(LANGUAGES),state="readonly",width=14)
            combo.bind("<<ComboboxSelected>>",a.outgoing_chat._languages_changed)
        combo.pack(side="right",fill="x",expand=True,padx=(8,0))
        detail=txt(foreground,"",10,MUTED,bg="#26201A")
        detail.pack(fill="x",padx=6)
        setattr(self,kind+"_detail",detail)
        # Full translation controls live in the Settings/Translation section.

    def _monitor(self,parent):
        a=self.app
        from wwii_dashboard import tactical_action
        border=MetalCanvas(parent)
        border.pack(fill="both",expand=True)
        box=tk.Frame(border,bg="#24221D",height=318 if self.compact else 492 if self.large_dpi else 390)
        box.pack(fill="both",expand=True,padx=12,pady=12)
        box.pack_propagate(False)
        head=tk.Frame(box,bg="#29261F",height=46)
        head.pack(fill="x")
        head.pack_propagate(False)
        from dashboard_ui import ui_photo
        tk.Label(head,image=ui_photo(head,"premium_radio.png"),bg="#29261F").pack(side="left",padx=(9,3))
        txt(head,local(a,"Мониторинг серверов","Моніторинг серверів","Server Monitor"),16,bold=True,bg="#29261F").pack(side="left",padx=4)
        self.friends_badge=txt(head,"",10,GREEN,bold=True)
        self.friends_badge.pack(side="right",padx=12)
        style=ttk.Style()
        style.configure("Monitor.Treeview",background="#191713",foreground=TEXT,
                        fieldbackground="#191713",rowheight=29,font=(FONT,10),borderwidth=0,
                        relief="flat")
        style.configure("Monitor.Treeview.Heading",background="#413326",foreground="#F4D49A",
                        bordercolor="#B48C52",lightcolor="#A9834F",darkcolor="#241A14",
                        font=(FONT,9,"bold"),padding=(3,5))
        style.map("Monitor.Treeview.Heading",background=[("active","#715032")])
        style.map("Monitor.Treeview",background=[("selected","#865A30")],
                  foreground=[("selected","#FFF0CF")])
        area=tk.Frame(box,bg="#161511")
        area.pack(fill="x",padx=8,pady=(2,5))
        columns=("star","name","map","players","ping","status")
        self.tree=ttk.Treeview(area,columns=columns,show="headings",height=2 if self.compact else 3,
                               style="Monitor.Treeview",selectmode="browse")
        names=("★",local(a,"Сервер","Сервер","Server"),local(a,"Карта","Мапа","Map"),
               local(a,"Игроки","Гравці","Players"),local(a,"Пинг","Пінг","Ping"),
               local(a,"Статус","Стан","Status"))
        for key,title,width in zip(columns,names,(34,178,90,82,64,98)):
            self.tree.heading(key,text=title,command=lambda k=key:self._sort(k))
            self.tree.column(key,width=width,minwidth=width,stretch=key=="name",
                             anchor="w" if key=="name" else "center")
        self.tree.tag_configure("offline",foreground="#AAA69F")
        self.tree.pack(side="left",fill="both",expand=True)
        sb=ttk.Scrollbar(area,orient="vertical",style="Premium.Vertical.TScrollbar",command=self.tree.yview)
        sb.pack(side="right",fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>",lambda _e:self._select())
        self.tree.bind("<Double-1>",lambda _e:self.connect_selected())
        heading=tk.Frame(box,bg="#302B23",height=29)
        heading.pack(fill="x",padx=8)
        self.player_title=txt(heading,"",10,AMBER,bold=True)
        self.player_title.pack(side="left",padx=7)
        self.last_update=txt(heading,"",9,MUTED)
        self.last_update.pack(side="right",padx=7)
        self.players=PlayerRoster(box,labels=(local(a,"Никнейм","Нікнейм","Nickname"),
                    local(a,"Счёт","Рахунок","Score"),local(a,"Пинг","Пінг","Ping")),
                    rows=2 if self.compact and self.dpi>=1.65 else 3 if self.compact or self.dpi>=1.6 else 4)
        self.players.pack(fill="both",expand=True,padx=8,pady=(0,4))
        actions=tk.Frame(box,bg="#24221D")
        actions.pack(fill="x",padx=7,pady=(0,7))
        for title,command,primary,icon in (
            (local(a,"Добавить сервер","Додати сервер","Add server"),
             lambda:self.dashboard.navigate("servers",add=True),False,"configure"),
            (local(a,"Обновить","Оновити","Refresh"),a.monitor.refresh,False,"updates"),
            (local(a,"Подключиться","Підключитися","Connect"),self.connect_selected,True,"test"),
        ):
            tactical_action(actions,title,command,primary=primary,
                            icon=None if self.large_dpi and self.app.root.winfo_screenwidth()<=1366 else icon).pack(
                            side="left",fill="x",expand=True,padx=2)

    def _rail(self):
        a=self.app
        from wwii_dashboard import tactical_action
        border=MetalCanvas(self.content,height=86 if self.large_dpi else 80 if self.compact else 78)
        border.pack(fill="x",padx=14,pady=(0,6))
        frame=tk.Frame(border,bg="#24211B",height=61 if self.compact else 70 if self.large_dpi else 62)
        frame.pack(fill="both",expand=True,padx=12,pady=8)
        frame.pack_propagate(False)
        for col in range(3):frame.columnconfigure(col,weight=1,uniform="rail")
        cells=[tk.Frame(frame,bg="#24211B") for _ in range(3)]
        for col,cell in enumerate(cells):cell.grid(row=0,column=col,sticky="nsew",padx=12,pady=4)
        txt(cells[0],"◈  "+local(a,"Оверлей в игре","Оверлей у грі","Game overlay"),12,bold=True).pack(anchor="w")
        actions=tk.Frame(cells[0],bg="#24211B")
        actions.pack(anchor="w")
        a.overlay_edit_button=tactical_action(actions,local(a,"Место","Місце","Position"),a.toggle_overlay_edit)
        a.overlay_edit_button.pack(side="left",padx=(0,4))
        tactical_action(actions,local(a,"Настроить →","Налаштувати →","Configure →"),
                        lambda:self.dashboard.navigate("overlay")).pack(side="left")
        txt(cells[1],"▧  Smart Engine",12,bold=True).pack(anchor="w")
        self.dashboard.engine_engine_bullet=txt(cells[1],"●",10,GREEN)
        self.dashboard.engine_engine_bullet.pack(side="left")
        self.dashboard.engine_engine_label=txt(cells[1],"",10)
        self.dashboard.engine_engine_label.pack(side="left")
        self.dashboard.engine_pack_label=txt(cells[1],"",9,MUTED)
        self.dashboard.engine_pack_label.pack(side="left",padx=5)
        txt(cells[2],"◉  "+local(a,"Состояние программы","Стан програми","Application status"),12,bold=True).pack(anchor="w")
        self.system_status=txt(cells[2],"",10,GREEN)
        self.system_status.pack(anchor="w")

    def _rows(self):
        rows=[]
        for s in self.app.monitor_settings["servers"]:
            snap=self.app.monitor.snapshots.get(s.address)
            state=snap.state if snap else "waiting"
            status=local(self.app,"Онлайн","Онлайн","Online") if state=="online" else (
                local(self.app,"Частично","Частково","Partial") if state=="limited" else
                local(self.app,"Нет ответа","Немає відповіді","No response") if state=="offline" else "…")
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
        previous=self.selected
        for item in self.tree.get_children():self.tree.delete(item)
        for address,values,state in self._rows():
            self.tree.insert("","end",iid=address,values=values,
                             tags=("offline",) if state not in ("online","limited") else ())
        if previous not in self.tree.get_children():
            previous=self.tree.get_children()[0] if self.tree.get_children() else None
        if previous:self.tree.selection_set(previous);self.selected=previous
        self._render_players()
        names={normalized_name(f) for f in self.app.monitor_settings["friends"]}
        online={(normalized_name(p.name),s.address) for s in self.app.monitor_settings["servers"]
                for snap in [self.app.monitor.snapshots.get(s.address)]
                if snap and snap.state=="online" for p in snap.players
                if normalized_name(p.name) in names}
        self.friends_badge.configure(text=local(self.app,"Друзья в игре: ","Друзі у грі: ","Friends online: ")+str(len(online)))
        enabled=bool(self.app.enabled_var.get() or self.app.outgoing_chat.enabled_var.get())
        self.system_status.configure(
            text=local(self.app,"Переводчик готов","Перекладач готовий","Translator ready") if enabled else
                 local(self.app,"Перевод выключен","Переклад вимкнено","Translation off"),
            fg=GREEN if enabled else MUTED)
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
