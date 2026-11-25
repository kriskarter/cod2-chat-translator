"""Server library, friend nicknames and live selected-server details."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from dashboard_ui import BG,CARD,TEXT,MUTED,AMBER,GREEN,FONT
from premium_home import local,txt
from server_monitor import Server,canonical_address,normalized_name,plain_name,color_runs,MAX_SERVERS
from premium_material import MetalCanvas
from premium_roster import PlayerRoster


class ServerPage:
    def __init__(self,dashboard,page):
        self.dashboard,self.app,self.page=dashboard,dashboard.app,page
        self.filter=tk.StringVar()
        self.player_filter=tk.StringVar()
        self.player_sort=tk.StringVar(value="Score")
        self._build()

    def _build(self):
        a=self.app
        from wwii_dashboard import tactical_action
        canvas=tk.Canvas(self.page,bg=BG,highlightthickness=0,borderwidth=0)
        scrollbar=ttk.Scrollbar(self.page,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left",fill="both",expand=True)
        scrollbar.pack(side="right",fill="y")
        content=tk.Frame(canvas,bg=BG)
        window=canvas.create_window((0,0),window=content,anchor="nw")
        content.bind("<Configure>",lambda _e:canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",lambda e:canvas.itemconfigure(window,width=e.width))
        self.scroll_canvas=canvas
        outer=tk.Frame(content,bg=BG)
        outer.pack(fill="both",expand=True,padx=16,pady=12)
        txt(outer,local(a,"СЕРВЕРЫ И ИГРОКИ","СЕРВЕРИ ТА ГРАВЦІ","SERVERS AND PLAYERS"),19,AMBER,True,bg=BG).pack(anchor="w",pady=(0,10))
        toolbar=tk.Frame(outer,bg=BG)
        toolbar.pack(fill="x",pady=(0,9))
        txt(toolbar,local(a,"Поиск","Пошук","Search"),10,bg=BG).pack(side="left",padx=(0,6))
        entry=ttk.Entry(toolbar,textvariable=self.filter,width=30)
        entry.pack(side="left",padx=(0,12))
        self.filter.trace_add("write",lambda *_:self.render())
        for caption,command,primary in (
            (local(a,"Добавить","Додати","Add"),self.add,True),
            (local(a,"Изменить","Змінити","Edit"),self.edit,False),
            (local(a,"Удалить","Видалити","Remove"),self.remove,False),
            (local(a,"★ Избранное","★ Обране","★ Favorite"),self.favorite,False),
            (local(a,"Обновить","Оновити","Refresh"),a.monitor.refresh,False),
        ):
            tactical_action(toolbar,caption,command,primary=primary).pack(side="left",padx=3)
        body=tk.Frame(outer,bg=BG)
        body.pack(fill="both",expand=True)
        body.columnconfigure(0,weight=3)
        body.columnconfigure(1,weight=2)
        left_shell=MetalCanvas(body,height=510)
        right_shell=MetalCanvas(body,height=510)
        left=tk.Frame(left_shell,bg=CARD)
        right=tk.Frame(right_shell,bg=CARD)
        left.pack(fill="both",expand=True,padx=11,pady=11)
        right.pack(fill="both",expand=True,padx=11,pady=11)
        left_shell.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right_shell.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        body.rowconfigure(0,weight=1)
        txt(left,local(a,"Отслеживаемые серверы","Відстежувані сервери","Tracked servers"),13,AMBER,True).pack(anchor="w",padx=10,pady=8)
        self.listbox=tk.Listbox(left,bg="#191815",fg=TEXT,selectbackground="#7B5026",
                                selectforeground="#FFF0D4",bd=0,highlightthickness=0,
                                font=(FONT,11),height=5,activestyle="none")
        self.listbox.pack(fill="x",padx=9,pady=(0,8))
        self.listbox.bind("<<ListboxSelect>>",lambda _e:self.details())
        self.listbox.bind("<Double-1>",lambda _e:self.connect())
        bottom=tk.Frame(left,bg=CARD)
        bottom.pack(fill="x",padx=9,pady=(0,8))
        tactical_action(bottom,local(a,"Подключиться","Підключитися","Connect"),self.connect,primary=True,icon="test").pack(side="left",padx=3)
        tactical_action(bottom,local(a,"Копировать адрес","Копіювати адресу","Copy address"),self.copy).pack(side="left",padx=3)
        self.summary=txt(bottom,"",9,MUTED)
        self.summary.pack(side="right",padx=4)
        roster=tk.Frame(left,bg=CARD)
        roster.pack(fill="both",expand=True,padx=9,pady=(0,8))
        search_row=tk.Frame(roster,bg=CARD)
        search_row.pack(fill="x")
        txt(search_row,local(a,"Игроки","Гравці","Players"),11,AMBER,True).pack(side="left")
        ttk.Entry(search_row,textvariable=self.player_filter,width=17).pack(side="left",padx=8)
        self.player_filter.trace_add("write",lambda *_:self.details())
        sort=ttk.Combobox(search_row,textvariable=self.player_sort,values=("Score","Ping","Name"),
                          state="readonly",width=7)
        sort.pack(side="right")
        sort.bind("<<ComboboxSelected>>",lambda _e:self.details())
        self.roster=PlayerRoster(roster,labels=(local(a,"Никнейм","Нікнейм","Nickname"),
                           local(a,"Счёт","Рахунок","Score"),local(a,"Пинг","Пінг","Ping")),rows=6)
        self.roster.pack(fill="both",expand=True,pady=(5,0))
        txt(right,local(a,"Сведения о сервере","Відомості про сервер","Server details"),13,AMBER,True).pack(anchor="w",padx=10,pady=8)
        self.info=txt(right,"",11,bg=CARD)
        self.info.configure(justify="left",anchor="nw",wraplength=380)
        self.info.pack(fill="x",padx=10,pady=(0,12))
        txt(right,local(a,"Избранные игроки","Обрані гравці","Favorite players"),13,AMBER,True).pack(anchor="w",padx=10,pady=5)
        self.friends=tk.Listbox(right,bg="#191815",fg=GREEN,selectbackground="#7B5026",
                                selectforeground="#FFF0D4",bd=0,highlightthickness=0,
                                font=(FONT,10),height=4,activestyle="none")
        self.friends.pack(fill="x",padx=9,pady=5)
        buttons=tk.Frame(right,bg=CARD)
        buttons.pack(fill="x",padx=8,pady=(0,7))
        tactical_action(buttons,local(a,"＋ Игрок","＋ Гравець","＋ Player"),self.add_friend).pack(side="left",padx=2)
        tactical_action(buttons,local(a,"Удалить","Видалити","Remove"),self.remove_friend).pack(side="left",padx=2)
        self.notify=tk.BooleanVar(value=a.monitor_settings["notify_friends"])
        tk.Checkbutton(right,text=local(a,"Уведомлять о появлении друга","Сповіщати про появу друга","Notify when a friend appears"),
                       variable=self.notify,command=self._notify_changed,
                       bg=CARD,fg=TEXT,selectcolor=CARD,activebackground=CARD,
                       activeforeground=TEXT,font=(FONT,10)).pack(anchor="w",padx=8,pady=(0,4))
        interval=tk.Frame(right,bg=CARD)
        interval.pack(fill="x",padx=10,pady=(0,8))
        txt(interval,local(a,"Автообновление, сек.","Автооновлення, с","Auto refresh, sec"),10,MUTED).pack(side="left")
        self.refresh_var=tk.StringVar(value=str(a.monitor_settings["refresh_seconds"]))
        combo=ttk.Combobox(interval,textvariable=self.refresh_var,values=("30","60","120","300","600"),state="readonly",width=5)
        combo.pack(side="left",padx=8)
        combo.bind("<<ComboboxSelected>>",lambda _e:self._interval_changed())
        self.render()

    def _selected(self):
        selection=self.listbox.curselection()
        if not selection:return None
        index=selection[0]
        return self._visible[index] if index<len(self._visible) else None

    def render(self):
        selected=self._selected() if hasattr(self,"_visible") else None
        term=self.filter.get().strip().casefold()
        self._visible=[s for s in self.app.monitor_settings["servers"]
                       if term in (s.label+" "+s.address+" "+
                                   (self.app.monitor.snapshots.get(s.address).name if self.app.monitor.snapshots.get(s.address) else "")).casefold()]
        self._visible.sort(key=lambda s:(not s.favorite,(s.label or s.address).casefold()))
        position=self.listbox.yview()[0]
        labels=[]
        for s in self._visible:
            snap=self.app.monitor.snapshots.get(s.address)
            marker="●" if snap and snap.state in ("online","limited") else "○"
            labels.append(f"{'★' if s.favorite else '☆'}  {marker}  {s.label or (snap.name if snap else s.address)}   ·   {s.address}")
        if tuple(self.listbox.get(0,"end"))!=tuple(labels):
            self.listbox.delete(0,"end")
            for label in labels:self.listbox.insert("end",label)
        if self._visible:
            index=self._visible.index(selected) if selected in self._visible else 0
            self.listbox.selection_clear(0,"end")
            self.listbox.selection_set(index)
            self.listbox.yview_moveto(position)
        friend_rows=[]
        for friend in self.app.monitor_settings["friends"]:
            present=[s.label or s.address for s in self.app.monitor_settings["servers"]
                     for snap in [self.app.monitor.snapshots.get(s.address)]
                     if snap and snap.state=="online"
                     and any(normalized_name(p.name)==normalized_name(friend) for p in snap.players)]
            friend_rows.append(f"{'●' if present else '○'}  {friend}"+("  ·  "+", ".join(present) if present else ""))
        if tuple(self.friends.get(0,"end"))!=tuple(friend_rows):
            friend_position=self.friends.yview()[0]
            self.friends.delete(0,"end")
            for row in friend_rows:self.friends.insert("end",row)
            self.friends.yview_moveto(friend_position)
        self.summary.configure(text=f"{len(self._visible)}/{len(self.app.monitor_settings['servers'])}")
        self.details()

    def details(self):
        a=self.app
        server=self._selected()
        snap=a.monitor.snapshots.get(server.address) if server else None
        if not server:
            self.info.configure(text=local(a,"Добавьте сервер для мониторинга.","Додайте сервер для моніторингу.","Add a server to monitor."))
            self._roster(None)
            return
        state=local(a,"Онлайн","Онлайн","Online") if snap and snap.state=="online" else (
            local(a,"Частичный ответ","Часткова відповідь","Partial response") if snap and snap.state=="limited"
            else local(a,"Нет ответа","Немає відповіді","No response"))
        lines=[server.label or (snap.name if snap else server.address),server.address,"",
               local(a,"Состояние: ","Стан: ","State: ")+state]
        if snap and snap.state in ("online","limited"):
            lines.extend((local(a,"Карта: ","Мапа: ","Map: ")+(snap.map_name or "—"),
                          local(a,"Режим: ","Режим: ","Mode: ")+(snap.game_type or "—"),
                          local(a,"Игроки: ","Гравці: ","Players: ")+f"{snap.clients if snap.clients is not None else '—'}/{snap.max_clients if snap.max_clients is not None else '—'}",
                          local(a,"Ответ: ","Відповідь: ","Response: ")+str(snap.ping_ms)+" ms"))
        lines.append(local(a,"Последний успех: ","Остання успішна відповідь: ","Last success: ")+
                     (snap.last_success.astimezone().strftime("%H:%M:%S") if snap and snap.last_success else "—"))
        if snap and snap.state=="limited":lines.append(local(a,"Список игроков сервер не предоставил.","Список гравців сервер не надав.","Server did not provide a player list."))
        self.info.configure(text="\n".join(lines))
        self._roster(snap)

    def _roster(self,snap):
        a=self.app
        players=[]
        if snap and snap.state=="online":
            term=normalized_name(self.player_filter.get())
            players=[p for p in snap.players if term in normalized_name(p.name)]
            if self.player_sort.get()=="Ping":
                players.sort(key=lambda p:(p.ping is None,p.ping or 0,p.name.casefold()))
            elif self.player_sort.get()=="Name":
                players.sort(key=lambda p:p.name.casefold())
            else:
                players.sort(key=lambda p:(-(p.score or 0),p.name.casefold()))
        empty=(local(a,"Совпадений нет.","Збігів немає.","No matches.") if snap and snap.state=="online" else
               local(a,"Список игроков недоступен.","Список гравців недоступний.","Player list unavailable."))
        self.roster.render(players,friends=a.monitor_settings["friends"],empty=empty)

    def update_snapshot(self,snapshot):
        if self.page.winfo_exists():self.render()

    def _save(self):
        self.app._persist_settings()
        self.app.monitor.refresh()
        self.render()
        if hasattr(self.dashboard,"premium_home"):self.dashboard.premium_home.render()

    def _editor(self,current=None):
        a=self.app
        window=tk.Toplevel(a.root)
        window.title(local(a,"Сервер CoD2","Сервер CoD2","CoD2 server"))
        window.configure(bg=CARD)
        window.transient(a.root)
        window.grab_set()
        window.resizable(False,False)
        heading=tk.Frame(window,bg="#A6783D",padx=2,pady=2)
        heading.pack(fill="x",padx=12,pady=(12,3))
        plate=tk.Frame(heading,bg="#2B2821")
        plate.pack(fill="x")
        txt(plate,local(a,"ИЗМЕНИТЬ СЕРВЕР" if current else "ДОБАВИТЬ СЕРВЕР",
                        "ЗМІНИТИ СЕРВЕР" if current else "ДОДАТИ СЕРВЕР",
                        "EDIT SERVER" if current else "ADD SERVER"),
            13,AMBER,True,bg="#2B2821").pack(anchor="w",padx=11,pady=8)
        address=tk.StringVar(value=current.address if current else "")
        name=tk.StringVar(value=current.label if current else "")
        favorite=tk.BooleanVar(value=current.favorite if current else True)
        for caption,var in ((local(a,"Адрес IP/домен:порт","Адреса IP/домен:порт","IP/domain:port"),address),
                            (local(a,"Название (необязательно)","Назва (необов’язково)","Label (optional)"),name)):
            txt(window,caption,11,bg=CARD).pack(anchor="w",padx=18,pady=(12,2))
            ttk.Entry(window,textvariable=var,width=38).pack(fill="x",padx=18)
        tk.Checkbutton(window,text=local(a,"В избранное","До обраного","Favorite"),variable=favorite,
                       bg=CARD,fg=TEXT,selectcolor=CARD,activebackground=CARD,
                       activeforeground=TEXT).pack(anchor="w",padx=16,pady=10)
        error=txt(window,"",9,"#F5A389",bg=CARD)
        error.pack(anchor="w",padx=18)
        def save():
            try:canonical=canonical_address(address.get())
            except ValueError:
                error.configure(text=local(a,"Проверьте адрес и порт.","Перевірте адресу та порт.","Check host and port."))
                return
            servers=a.monitor_settings["servers"]
            if any(s.address==canonical and s!=current for s in servers):
                error.configure(text=local(a,"Сервер уже добавлен.","Сервер уже додано.","Server already exists."))
                return
            if current is None and len(servers)>=MAX_SERVERS:
                error.configure(text=local(a,"Лимит: 32 сервера.","Ліміт: 32 сервери.","Limit: 32 servers."))
                return
            entry=Server(canonical,name.get().strip()[:80],bool(favorite.get()))
            with a.monitor._lock:
                if current:servers[servers.index(current)]=entry
                else:servers.append(entry)
            window.destroy()
            self._save()
        from wwii_dashboard import tactical_action
        actions=tk.Frame(window,bg=CARD)
        actions.pack(fill="x",padx=18,pady=(8,16))
        tactical_action(actions,local(a,"Сохранить","Зберегти","Save"),save,primary=True).pack(side="left",fill="x",expand=True,padx=(0,5))
        tactical_action(actions,local(a,"Отмена","Скасувати","Cancel"),window.destroy).pack(side="left",fill="x",expand=True)
        window.bind("<Return>",lambda _e:save())
        window.bind("<Escape>",lambda _e:window.destroy())
        window.geometry(f"+{a.root.winfo_rootx()+150}+{a.root.winfo_rooty()+100}")
        window.wait_window()

    def add(self):self._editor()
    def edit(self):
        selected=self._selected()
        if selected:self._editor(selected)
    def remove(self):
        selected=self._selected()
        if not selected:return
        if not messagebox.askyesno(local(self.app,"Удалить сервер?","Видалити сервер?","Remove server?"),
                selected.label or selected.address,parent=self.app.root):return
        with self.app.monitor._lock:self.app.monitor_settings["servers"].remove(selected)
        self.app.monitor.snapshots.pop(selected.address,None)
        self._save()
    def favorite(self):
        selected=self._selected()
        if selected:
            servers=self.app.monitor_settings["servers"]
            with self.app.monitor._lock:servers[servers.index(selected)]=Server(selected.address,selected.label,not selected.favorite)
            self._save()
    def connect(self):
        selected=self._selected()
        if selected:self.app._launch_server(selected.address,selected.label)
    def copy(self):
        selected=self._selected()
        if selected:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(selected.address)
            self.app.status_var.set(selected.address)
    def add_friend(self):
        a=self.app
        from wwii_dashboard import tactical_action
        dialog=tk.Toplevel(a.root)
        dialog.title(local(a,"Избранный игрок","Обраний гравець","Favorite player"))
        dialog.configure(bg=CARD)
        dialog.transient(a.root)
        dialog.grab_set()
        dialog.resizable(False,False)
        heading=tk.Frame(dialog,bg="#A6783D",padx=2,pady=2)
        heading.pack(fill="x",padx=12,pady=(12,3))
        txt(heading,local(a,"ИЗБРАННЫЙ ИГРОК","ОБРАНИЙ ГРАВЕЦЬ","FAVORITE PLAYER"),
            13,AMBER,True,bg="#29251E").pack(fill="x",padx=9,pady=6)
        txt(dialog,local(a,"Никнейм игрока","Нікнейм гравця","Player nickname"),
            13,AMBER,True,bg=CARD).pack(anchor="w",padx=18,pady=(15,6))
        field=ttk.Entry(dialog,width=38)
        field.pack(fill="x",padx=18)
        value=None
        def save():
            nonlocal value
            value=field.get().strip()
            dialog.destroy()
        actions=tk.Frame(dialog,bg=CARD)
        actions.pack(fill="x",padx=18,pady=(12,16))
        tactical_action(actions,local(a,"Сохранить","Зберегти","Save"),save,primary=True).pack(
            side="left",fill="x",expand=True,padx=(0,5))
        tactical_action(actions,local(a,"Отмена","Скасувати","Cancel"),dialog.destroy).pack(
            side="left",fill="x",expand=True)
        dialog.bind("<Return>",lambda _e:save())
        dialog.bind("<Escape>",lambda _e:dialog.destroy())
        dialog.geometry(f"+{a.root.winfo_rootx()+170}+{a.root.winfo_rooty()+130}")
        field.focus_set()
        dialog.wait_window()
        if value is None:return
        name=plain_name(value)[:48]
        if name and normalized_name(name) not in {normalized_name(f) for f in a.monitor_settings["friends"]}:
            a.monitor_settings["friends"].append(name)
            self._save()
    def remove_friend(self):
        selection=self.friends.curselection()
        if selection:
            del self.app.monitor_settings["friends"][selection[0]]
            self._save()
    def _notify_changed(self):
        self.app.monitor_settings["notify_friends"]=bool(self.notify.get())
        self.app._persist_settings()
    def _interval_changed(self):
        with self.app.monitor._lock:self.app.monitor_settings["refresh_seconds"]=int(self.refresh_var.get())
        self.app._persist_settings()
        self.app.monitor.refresh()
