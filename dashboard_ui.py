"""Modern Esports Utility: real Tk/ttk desktop dashboard, no static screenshot.

The UI only binds to existing ControlApp variables and callback methods.
No translation, network, log scanning or game control runs in this module.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from server_catalog import FEATURED_SERVER

BG = "#17150F"
SIDEBAR = "#231F18"
CARD = "#24231D"
CARD_ALT = "#393329"
BORDER = "#9C7950"
TEXT = "#F6E9CB"
MUTED = "#D2BE99"
CYAN = "#F0B15B"
AMBER = "#FFB25D"
GREEN = "#91E06D"
DANGER = "#FF9B8A"
FONT = "Segoe UI"

# Only real configurable functions and actual application states appear here.
I18N = {
    "ru": {
        "home":"Главная", "translation":"Перевод", "overlay":"Оверлей",
        "knowledge":"База знаний", "stats":"Статистика", "settings":"Настройки",
        "about":"О программе", "tagline":"Умный перевод игрового чата",
        "ready":"РЕЖИМ ПЕРЕВОДА", "home_head":"Центр управления",
        "home_sub":"Настройки F8, F9 и игровые инструменты в одном окне",
        "server":"Быстрое подключение", "profile":"Выбор сервера",
        "connect":"Подключиться", "server_settings":"Настройки сервера",
        "smart":"Smart Engine", "knowledge_state":"Локальные знания",
        "free_services":"Резервный онлайн-перевод",
        "f8":"Входящий перевод · F8", "f9":"Исходящий перевод · F9",
        "target":"Переводить на", "my_language":"Мой язык",
        "send_language":"Отправлять на", "enabled":"Включён",
        "smart_enabled":"Smart Engine", "slang":"Игровой сленг",
        "dedupe":"Убирать повторы", "original":"Показывать оригинал",
        "hide_same":"Не дублировать выбранный язык",
        "style":"Стиль перевода", "other":"Другой язык",
        "hotkeys":"Горячие клавиши", "f8_note":"Оверлей: новые сообщения игроков",
        "f9_note":"Написание и перевод своих сообщений прямо в игре",
        "overlay_view":"Оверлей в игре", "font_size":"Размер текста",
        "opacity":"Прозрачность фона", "time":"Время показа",
        "messages":"Сообщений", "bg_only":"Фон только при сообщениях",
        "compact_bg":"Подложка по размеру текста", "fade":"Плавное появление",
        "text_only":"Только текст", "minimal":"Минимальный",
        "readable":"Читаемый", "standard":"Стандартное место",
        "test":"Тест оверлея", "clear":"Очистить",
        "configure":"Настроить оверлей", "borderless":"CoD2 → поверх",
        "screenshot":"Скриншот · F10",
        "quick":"Быстрые действия", "update_knowledge":"Обновить знания",
        "export":"Экспорт базы", "learn":"Управление базой",
        "latency":"Фактическая статистика F8", "no_samples":"Пока нет измерений",
        "translation_head":"Настройки перевода",
        "overlay_head":"Отображение поверх игры",
        "settings_head":"Параметры программы",
        "settings_sub":"Серверы, язык интерфейса и системные действия",
        "interface":"Язык интерфейса", "updates":"Проверить обновления",
        "cod2":"Окно CoD2", "app_active":"Переводчик включён",
        "last":"Последнее событие", "no_data":"Переводы ещё не измерялись",
        "online_hint":"Используются при необходимости",
        "overlay_hint":"Изменения сразу применяются к игровому оверлею",
        "actual":"Показаны реальные настройки и измерения",
        "base":"Групп выражений", "live":"Действующая база",
        "enter_hint":"F9 — исходящие сообщения", "privacy":"Без автоматической отправки собранных сообщений",
        "engine_mode":"Режим", "f8_label":"Входящий F8", "f9_label":"Исходящий F9",
        "support":"Работает на текущем профиле CoD2", "theme":"Modern Esports Utility",
    },
    "uk": {
        "home":"Головна", "translation":"Переклад", "overlay":"Оверлей",
        "knowledge":"База знань", "stats":"Статистика", "settings":"Налаштування",
        "about":"Про програму", "tagline":"Розумний переклад ігрового чату",
        "ready":"РЕЖИМ ПЕРЕКЛАДУ", "home_head":"Центр керування",
        "home_sub":"Налаштування F8, F9 та ігрові інструменти в одному вікні",
        "server":"Швидке підключення", "profile":"Вибір сервера",
        "connect":"Підключитися", "server_settings":"Налаштування сервера",
        "smart":"Smart Engine", "knowledge_state":"Локальні знання",
        "free_services":"Резервний онлайн-переклад",
        "f8":"Вхідний переклад · F8", "f9":"Вихідний переклад · F9",
        "target":"Перекладати на", "my_language":"Моя мова",
        "send_language":"Надсилати мовою", "enabled":"Увімкнено",
        "smart_enabled":"Smart Engine", "slang":"Ігровий сленг",
        "dedupe":"Прибирати повтори", "original":"Показувати оригінал",
        "hide_same":"Не дублювати обрану мову",
        "style":"Стиль перекладу", "other":"Інша мова",
        "hotkeys":"Гарячі клавіші", "f8_note":"Оверлей: нові повідомлення гравців",
        "f9_note":"Написання й переклад своїх повідомлень у грі",
        "overlay_view":"Оверлей у грі", "font_size":"Розмір тексту",
        "opacity":"Прозорість тла", "time":"Час показу",
        "messages":"Повідомлень", "bg_only":"Тло лише за повідомлень",
        "compact_bg":"Підкладка за розміром тексту", "fade":"Плавна поява",
        "text_only":"Лише текст", "minimal":"Мінімальний",
        "readable":"Читабельний", "standard":"Стандартне місце",
        "test":"Тест оверлею", "clear":"Очистити",
        "configure":"Налаштувати оверлей", "borderless":"CoD2 → поверх",
        "screenshot":"Знімок екрана · F10",
        "quick":"Швидкі дії", "update_knowledge":"Оновити знання",
        "export":"Експорт бази", "learn":"Керування базою",
        "latency":"Фактична статистика F8", "no_samples":"Поки немає вимірювань",
        "translation_head":"Налаштування перекладу",
        "overlay_head":"Відображення поверх гри",
        "settings_head":"Параметри програми",
        "settings_sub":"Сервери, мова інтерфейсу й системні дії",
        "interface":"Мова інтерфейсу", "updates":"Перевірити оновлення",
        "cod2":"Вікно CoD2", "app_active":"Перекладач увімкнено",
        "last":"Остання подія", "no_data":"Переклади ще не вимірювалися",
        "online_hint":"Використовуються за потреби",
        "overlay_hint":"Зміни одразу застосовуються до ігрового оверлею",
        "actual":"Показано реальні налаштування й вимірювання",
        "base":"Груп виразів", "live":"Чинна база",
        "enter_hint":"F9 — вихідні повідомлення", "privacy":"Без автоматичного надсилання зібраних повідомлень",
        "engine_mode":"Режим", "f8_label":"Вхідний F8", "f9_label":"Вихідний F9",
        "support":"Працює з поточним профілем CoD2", "theme":"Modern Esports Utility",
    },
    "en": {
        "home":"Home", "translation":"Translation", "overlay":"Overlay",
        "knowledge":"Knowledge", "stats":"Statistics", "settings":"Settings",
        "about":"About", "tagline":"Intelligent in-game chat translation",
        "ready":"TRANSLATION MODE", "home_head":"Command center",
        "home_sub":"F8, F9 and game utilities in one place",
        "server":"Quick connect", "profile":"Server selection",
        "connect":"Connect", "server_settings":"Server settings",
        "smart":"Smart Engine", "knowledge_state":"Local knowledge",
        "free_services":"Fallback online translation",
        "f8":"Incoming translation · F8", "f9":"Outgoing translation · F9",
        "target":"Translate to", "my_language":"My language",
        "send_language":"Send as", "enabled":"Enabled",
        "smart_enabled":"Smart Engine", "slang":"Gaming slang",
        "dedupe":"Remove duplicates", "original":"Show original",
        "hide_same":"Skip selected language",
        "style":"Translation style", "other":"Other language",
        "hotkeys":"Hotkeys", "f8_note":"Overlay: messages from other players",
        "f9_note":"Compose and translate your messages in game",
        "overlay_view":"In-game overlay", "font_size":"Text size",
        "opacity":"Background opacity", "time":"Display time",
        "messages":"Messages", "bg_only":"Background only with messages",
        "compact_bg":"Fit backdrop to text", "fade":"Smooth fade",
        "text_only":"Text only", "minimal":"Minimal",
        "readable":"Readable", "standard":"Default position",
        "test":"Test overlay", "clear":"Clear",
        "configure":"Configure overlay", "borderless":"CoD2 → borderless",
        "screenshot":"Screenshot · F10",
        "quick":"Quick actions", "update_knowledge":"Update knowledge",
        "export":"Export data", "learn":"Manage knowledge",
        "latency":"Actual F8 statistics", "no_samples":"No samples yet",
        "translation_head":"Translation settings",
        "overlay_head":"In-game overlay settings",
        "settings_head":"Application settings",
        "settings_sub":"Servers, display language and system controls",
        "interface":"Interface language", "updates":"Check for updates",
        "cod2":"CoD2 window", "app_active":"Translator enabled",
        "last":"Last event", "no_data":"No translation timing yet",
        "online_hint":"Used when needed",
        "overlay_hint":"Changes apply to the game overlay immediately",
        "actual":"Real settings and measured values",
        "base":"Phrase groups", "live":"Active pack",
        "enter_hint":"F9 — outgoing messages", "privacy":"No automatic upload of collected messages",
        "engine_mode":"Mode", "f8_label":"Incoming F8", "f9_label":"Outgoing F9",
        "support":"Uses your current CoD2 log profile", "theme":"Modern Esports Utility",
    },
}


def setup_theme(root: tk.Tk):
    style = ttk.Style(root)
    compact_dpi = float(root.tk.call("tk", "scaling")) >= 1.6
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure(".", font=(FONT, 10), background=BG, foreground=TEXT)
    style.configure("Dash.TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=(FONT, 10))
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED, font=(FONT, 10))
    style.configure("CardHead.TLabel", background=CARD, foreground=TEXT, font=(FONT, 12, "bold"))
    style.configure("Body.TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("TButton", background="#3D3528", foreground=TEXT,
                    font=(FONT, 10, "bold"), bordercolor="#99774C",
                    lightcolor="#94744C", darkcolor="#17130F",
                    borderwidth=2, padding=(8, 5), relief="raised")
    style.map("TButton", background=[("pressed", "#6A502E"), ("active", "#554027")],
              foreground=[("disabled", MUTED), ("active", TEXT)])
    style.configure("Accent.TButton", background="#9E4E0B", foreground="#FFFFFF",
                    font=(FONT, 10, "bold"), bordercolor="#F3AC52",
                    lightcolor="#EC9E40", darkcolor="#482002",
                    padding=(10, 5), borderwidth=2, relief="raised")
    style.map("Accent.TButton", background=[("active", "#C97212"), ("pressed", "#733804")])
    style.configure("Warm.TButton", background="#5E391A", foreground="#FFF1D5",
                    bordercolor="#BC8546", padding=(10, 5))
    style.map("Warm.TButton", background=[("active", "#BA681B"), ("pressed", "#4D2D0E")])
    style.configure("TCheckbutton", background=CARD, foreground=TEXT, padding=(2, 5))
    style.map("TCheckbutton", background=[("active", CARD)],
              foreground=[("disabled", MUTED)])
    style.configure("TCombobox", fieldbackground="#332C20", background=CARD_ALT,
                    foreground="#201B12", arrowcolor=AMBER, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, selectbackground="#B46B1C",
                    selectforeground=TEXT, padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", "#DCCBAD")],
              foreground=[("readonly", "#21190F")])
    style.configure("TScale", background=CARD, troughcolor="#473725", borderwidth=0)
    if "Premium.Scale.trough" not in style.element_names():
        style.element_create("Premium.Scale.trough", "image",
            ui_photo(root, "premium_scale_trough.png"),
            border=(9, 3, 9, 3), sticky="we")
        style.element_create("Premium.Scale.slider", "image",
            ui_photo(root, "premium_scale_thumb.png"), sticky="")
    style.layout("Horizontal.TScale", [
        ("Premium.Scale.trough", {"sticky": "we", "children": [
            ("Premium.Scale.slider", {"side": "left", "sticky": ""})]})])
    # Compact, metal-framed home actions. Advanced settings keep the
    # larger touch targets from their existing styles.
    style.configure("Tactical.TButton", background="#443728", foreground="#FFF0D3",
                    font=(FONT, 9, "bold"), bordercolor="#A78657",
                    lightcolor="#D0A16B", darkcolor="#18110A",
                    padding=(6, 3), borderwidth=2, relief="raised")
    style.map("Tactical.TButton",
              background=[("active", "#6B4E2D"), ("pressed", "#352316")],
              foreground=[("disabled", MUTED)])
    style.configure("TacticalAccent.TButton", background="#9C4A09",
                    foreground="#FFFFFF", font=(FONT, 9, "bold"),
                    bordercolor="#FFC06B", lightcolor="#E89A42",
                    darkcolor="#411C07", padding=(6, 3),
                    borderwidth=2, relief="raised")
    style.map("TacticalAccent.TButton",
              background=[("active", "#BE6A16"), ("pressed", "#7B3102")])
    style.configure("TSeparator", background=BORDER)
    # Image-backed, nine-slice controls use the exact same drawn material as
    # the navigation, cards and footer.  ttk retains native focus, keyboard
    # activation, disabled and pressed states and the existing callbacks.
    for group in ("metal", "amber"):
        images = {state: ui_photo(root, f"premium_{group}_{state}.png")
                  for state in ("normal", "hover", "pressed", "disabled")}
        element = f"Premium{group.title()}.surface"
        if element not in style.element_names():
            style.element_create(element, "image", images["normal"],
                ("disabled", images["disabled"]),
                ("pressed", images["pressed"]),
                ("active", images["hover"]),
                border=(13, 12, 13, 12), sticky="nsew")
        layout = [(element, {"sticky":"nsew", "children":[
            ("Button.padding", {"sticky":"nsew", "children":[
                ("Button.label", {"sticky":"nsew"})]})]})]
        names = ("Accent.TButton", "TacticalAccent.TButton", "PremiumNavActive.TButton") if group == "amber" else (
            "TButton", "Tactical.TButton", "Warm.TButton", "PremiumNav.TButton")
        for name in names:
            style.layout(name, layout)
            style.configure(name, foreground="#FFF0D1", background=CARD,
                            borderwidth=0, padding=(5, 2) if compact_dpi else (8, 4),
                            relief="flat")
            style.map(name, foreground=[("disabled", "#A4977E"),
                                         ("active", "#FFFFFF")])
    for name in ("PremiumNav.TButton", "PremiumNavActive.TButton"):
        style.configure(name, font=(FONT, 9 if compact_dpi else 10, "bold"),
                        padding=(3, 2) if compact_dpi else (4, 3))
    for name in ("Tactical.TButton", "TacticalAccent.TButton"):
        style.configure(name, padding=(4, 2) if compact_dpi else (7, 3))
    if "Premium.Generic.surface" not in style.element_names():
        style.element_create("Premium.Generic.surface", "image",
            ui_photo(root, "premium_generic_frame.png"),
            border=(42, 42, 42, 42), sticky="nsew")
    style.layout("PremiumCard.TFrame", [("Premium.Generic.surface",
                  {"sticky":"nsew"})])
    style.configure("PremiumCard.TFrame", background=CARD)
    # Real readonly comboboxes and scales keep their native semantics.
    style.configure("TCombobox", fieldbackground="#252218", background="#382D20",
                    foreground=TEXT, arrowcolor=AMBER, bordercolor=BORDER,
                    selectbackground="#A75B11", selectforeground="#FFFFFF")
    style.map("TCombobox", fieldbackground=[("readonly", "#29251B")],
              foreground=[("readonly", TEXT)])


def tr(app, key):
    return I18N.get(app.ui_language, I18N["ru"]).get(key, key)


def text(parent, value, *, size=10, color=TEXT, bold=False,
         bg=None, wraplength=None, anchor="w"):
    return tk.Label(parent, text=value, bg=bg or parent.cget("bg"),
                    fg=color, font=(FONT, size, "bold" if bold else "normal"),
                    anchor=anchor, justify="left", wraplength=wraplength)


# UI art is raster background only. Labels, toggles and buttons remain real
# widgets with live callbacks; no baked telemetry or screenshot mockups.
_PHOTOS = {}


def ui_photo(master, name):
    from app import resource_path
    key=(str(master.tk), name)
    photo=_PHOTOS.get(key)
    if photo is None:
        photo=tk.PhotoImage(file=str(resource_path("assets/ui_wwii/"+name)))
        _PHOTOS[key]=photo
    return photo


def card(parent, title=None, *, tone=CYAN, padding=5):
    compact_dpi = float(parent.tk.call("tk", "scaling")) >= 1.6
    heading_height = 27 if compact_dpi else 30
    border=ttk.Frame(parent, style="PremiumCard.TFrame")
    shell=tk.Frame(border, bg="#1F1F19", padx=2, pady=2)
    shell.pack(fill="both", expand=True, padx=8, pady=8)
    if title:
        heading=tk.Canvas(shell, bg="#302B20", height=heading_height,
                          highlightthickness=0, borderwidth=0)
        heading.pack(fill="x")
        plate=ui_photo(parent, "premium_plate.png")
        heading.create_image(0,0,anchor="nw",image=plate)
        def adjust(event,plate=plate):
            heading.delete("repeat")
            for x in range(plate.width(),event.width+plate.width(),plate.width()):
                heading.create_image(x,0,anchor="nw",image=plate,tags="repeat")
        heading.bind("<Configure>", adjust)
        heading.create_text(17,heading_height//2,text=title.upper(),anchor="w",
                            font=("Bahnschrift SemiCondensed",11 if compact_dpi else 13,"bold"),
                            fill=TEXT)
        heading.create_line(2,heading_height-1,1152,heading_height-1,
                            fill="#B28B4B",width=1)
    box=tk.Frame(shell, bg=CARD,
                 padx=2 if compact_dpi else padding,
                 pady=2 if compact_dpi else padding)
    box.pack(fill="both",expand=True)
    return border,box


def check(parent, caption, var, fn):
    # The visual states are illustrated; Tk owns the value and the callback.
    return tk.Checkbutton(
        parent,text=caption,variable=var,command=fn,
        indicatoron=0,image=ui_photo(parent,"premium_check_off.png"),
        selectimage=ui_photo(parent,"premium_check_on.png"),
        compound="left",
        bg=CARD,fg=TEXT,activebackground=CARD,activeforeground=TEXT,
        selectcolor=CARD,font=(FONT,10),cursor="hand2",
        highlightcolor=AMBER,highlightbackground=CARD,highlightthickness=1,
        borderwidth=0,padx=4,pady=2,takefocus=True,
    )


def action(parent, caption, fn, *, primary=False, warm=False):
    style = "Accent.TButton" if primary else "Warm.TButton" if warm else "TButton"
    return ttk.Button(parent, text=caption, command=fn, style=style)


def label_combo(parent, caption, items, variable, callback, *, width=15):
    row = tk.Frame(parent, bg=CARD)
    text(row, caption, size=9, color=MUTED).pack(anchor="w", pady=(0, 5))
    combo = ttk.Combobox(row, values=items, textvariable=variable,
                         state="readonly", width=width)
    combo.pack(fill="x")
    combo.bind("<<ComboboxSelected>>", callback)
    return row, combo


class Dashboard:
    """One instance per rebuild. All live data is read on the Tk UI thread."""

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.page = "home"
        self.pages = {}
        self.nav_buttons = {}
        self.widgets = []
        self.engine_var = tk.StringVar(master=self.root)
        self.base_var = tk.StringVar(master=self.root)
        self.metrics_var = tk.StringVar(master=self.root)
        self.active_var = tk.StringVar(master=self.root)
        self.server_var = app.server_summary_var
        self.root.configure(background=BG)
        # The initial window geometry is set by ControlApp. Do not reset a
        # user-resized window every time interface language changes.
        self.root.minsize(1050, 650)
        setup_theme(self.root)
        self._build()
        self.refresh()
        self._tick()

    def _build(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)
        self.outer = outer
        head = tk.Frame(outer, bg=SIDEBAR, height=94)
        head.pack(fill="x")
        head.pack_propagate(False)
        mark = tk.Frame(head, bg=AMBER, width=5)
        mark.pack(side="left", fill="y")
        try:
            from app import resource_path
            logo = tk.PhotoImage(file=str(resource_path("assets/app_64.png")))
            self.app._logo_image = logo
            tk.Label(head, image=logo, bg=SIDEBAR).pack(side="left", padx=(20, 14))
        except Exception:
            text(head, "CoD2", bg=SIDEBAR, size=22, bold=True, color=AMBER).pack(side="left", padx=20)

        brand = tk.Frame(head, bg=SIDEBAR)
        brand.pack(side="left", fill="y", pady=14)
        text(brand, "CoD2 CHAT TRANSLATOR", bg=SIDEBAR, size=18, bold=True).pack(anchor="w")
        text(brand, tr(self.app, "tagline"), bg=SIDEBAR, size=10, color=MUTED).pack(anchor="w", pady=(3, 0))
        right = tk.Frame(head, bg=SIDEBAR)
        right.pack(side="right", padx=20)
        from app import APP_VERSION
        text(right, f"v{APP_VERSION}", color=CYAN, bg=SIDEBAR, bold=True).pack(anchor="e")
        text(right, tr(self.app, "theme"), bg=SIDEBAR, color=MUTED, size=9).pack(anchor="e", pady=(3, 0))
        # Original lightweight HUD artwork: drawn with Tk Canvas, not a
        # screenshot, externally hosted image or fake live telemetry.
        hud = tk.Canvas(head, width=210, height=72, bg=SIDEBAR,
                        borderwidth=0, highlightthickness=0)
        hud.pack(side="right", padx=(0, 26))
        for x in (18, 44, 70, 96, 122, 148, 174, 200):
            hud.create_line(x, 10, x, 61, fill="#1E3745")
        for y in (16, 36, 56):
            hud.create_line(15, y, 198, y, fill="#1E3745")
        hud.create_oval(71, 9, 139, 67, outline="#15768F", width=2)
        hud.create_arc(71, 9, 139, 67, start=25, extent=110,
                       style="arc", outline=CYAN, width=2)
        hud.create_arc(82, 19, 128, 57, start=205, extent=95,
                       style="arc", outline=AMBER, width=2)
        hud.create_line(105, 4, 105, 72, fill="#3D899C")
        hud.create_line(64, 38, 145, 38, fill="#3D899C")
        hud.create_oval(101, 34, 109, 42, fill=CYAN, outline="")
        hud.create_text(172, 70, text="F8 / F9", fill=CYAN,
                        font=(FONT, 8, "bold"))
        tk.Frame(outer, bg="#117A92", height=2).pack(fill="x")

        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True)
        sidebar = tk.Frame(body, bg=SIDEBAR, width=188)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        nav_text = tk.Frame(sidebar, bg=SIDEBAR)
        nav_text.pack(fill="x", pady=(24, 14), padx=15)
        text(nav_text, tr(self.app, "ready"), color=AMBER, bg=SIDEBAR, size=9, bold=True).pack(anchor="w")
        text(nav_text, "F8  /  F9", color=TEXT, bg=SIDEBAR, size=16, bold=True).pack(anchor="w", pady=(5, 0))
        navs = [
            ("home", "01", "home", lambda: self.navigate("home")),
            ("translation", "02", "translation", lambda: self.navigate("translation")),
            ("overlay", "03", "overlay", lambda: self.navigate("overlay")),
            ("knowledge", "04", "knowledge", lambda: self.navigate("knowledge")),
            ("stats", "05", "stats", lambda: self.navigate("stats")),
            ("settings", "06", "settings", lambda: self.navigate("settings")),
            ("about", "07", "about", self.app.show_about),
        ]
        for key, digit, label, cb in navs:
            btn = tk.Button(sidebar, text=f"{digit}    {tr(self.app, label)}",
                            bg=SIDEBAR, fg=MUTED, activebackground=CARD_ALT,
                            activeforeground=TEXT, bd=0,
                            relief="flat", font=(FONT, 11), anchor="w",
                            cursor="hand2", padx=17, pady=11, command=cb,
                            takefocus=True, highlightthickness=2,
                            highlightbackground=SIDEBAR, highlightcolor=CYAN)
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[key] = btn
        text(sidebar, "CoD2  /  TRANSLATOR", bg=SIDEBAR, color="#8BACC0", size=9).pack(
            side="bottom", anchor="w", padx=20, pady=20)

        stack = tk.Frame(body, bg=BG)
        stack.pack(side="left", fill="both", expand=True)
        self.stack = stack
        for name in ("home", "translation", "overlay", "knowledge", "stats", "settings"):
            page = tk.Frame(stack, bg=BG)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[name] = page
        self._home(self.pages["home"])
        self._translation(self.pages["translation"])
        self._overlay(self.pages["overlay"])
        self._knowledge(self.pages["knowledge"])
        self._stats(self.pages["stats"])
        self._settings(self.pages["settings"])
        if self.app.overlay_editing:
            for button_name in ("overlay_edit_button", "overlay_edit_button_alt"):
                button = getattr(self.app, button_name, None)
                if button is not None:
                    button.configure(text=self.app.t("lock_overlay"))
        for page in self.pages.values():
            self._enable_page_wheel(page)

        foot = tk.Frame(outer, bg=SIDEBAR, height=72)
        foot.pack(fill="x")
        foot.pack_propagate(False)
        row = tk.Frame(foot, bg=SIDEBAR)
        row.pack(fill="x", padx=19, pady=(9, 1))
        text(row, "●", size=13, color=GREEN, bg=SIDEBAR).pack(side="left")
        self.footer_engine = text(row, "", size=9, color=CYAN, bg=SIDEBAR, bold=True)
        self.footer_engine.pack(side="left", padx=(9, 20))
        text(row, " |  ", color=BORDER, bg=SIDEBAR).pack(side="left")
        text(row, "F8 / F9", color=MUTED, bg=SIDEBAR, bold=True).pack(side="left", padx=(10, 22))
        text(row, tr(self.app, "last")+":", color=MUTED, bg=SIDEBAR).pack(side="left")
        latest = tk.Label(row, textvariable=self.app.status_var, bg=SIDEBAR,
                          fg=TEXT, font=(FONT, 9), anchor="w", justify="left")
        latest.pack(side="left", fill="x", expand=True, padx=(10, 0))
        detail = tk.Label(foot, textvariable=self.app.last_var, bg=SIDEBAR,
                          fg=MUTED, font=(FONT, 9), anchor="w", justify="left")
        detail.pack(fill="x", padx=20)
        self.navigate("home")

    def _enable_page_wheel(self, page):
        """Scroll when hovering normal card text as well as the canvas gutter.

        Native comboboxes and sliders retain their own wheel interactions.
        """
        canvas = next(
            (child for child in page.winfo_children()
             if isinstance(child, tk.Canvas)),
            None,
        )
        if canvas is None:
            return

        def wheel(event):
            if not canvas.winfo_exists():
                return
            if getattr(event, "num", 0) in (4, 5):
                amount = -2 if event.num == 4 else 2
            else:
                delta = getattr(event, "delta", 0)
                amount = -1 if delta > 0 else 1 if delta < 0 else 0
            if amount:
                canvas.yview_scroll(amount, "units")

        def bind_tree(widget):
            if widget is not canvas and not isinstance(widget, (ttk.Scale, ttk.Combobox, ttk.Scrollbar)):
                widget.bind("<MouseWheel>", wheel, add="+")
                widget.bind("<Button-4>", wheel, add="+")
                widget.bind("<Button-5>", wheel, add="+")
            for child in widget.winfo_children():
                bind_tree(child)

        bind_tree(page)

    def _scroll_page(self, page, title, subtitle):
        canvas = tk.Canvas(page, bg=BG, highlightthickness=0, borderwidth=0)
        bar = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg=BG)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        # Mouse wheel is scoped to hovered page, never globally hijacked.
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta / 120), "units"))
        canvas.bind("<Button-4>", lambda _e: canvas.yview_scroll(-2, "units"))
        canvas.bind("<Button-5>", lambda _e: canvas.yview_scroll(2, "units"))
        self.widgets.append(canvas)
        header = tk.Frame(content, bg=BG)
        header.pack(fill="x", padx=22, pady=(17, 12))
        text(header, title, size=18, bold=True).pack(anchor="w")
        text(header, subtitle, size=10, color=MUTED).pack(anchor="w", pady=(4, 0))
        return content

    def _home(self, page):
        content = self._scroll_page(page, tr(self.app, "home_head"), tr(self.app, "home_sub"))
        grid = tk.Frame(content, bg=BG)
        grid.pack(fill="x", padx=22)
        grid.columnconfigure(0, weight=3, uniform="hgrid")
        grid.columnconfigure(1, weight=2, uniform="hgrid")
        left, server = card(grid, tr(self.app, "server"), tone=AMBER)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._server_card(server)
        right, engine = card(grid, tr(self.app, "smart"))
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        self._engine_card(engine)
        first, incoming = card(grid, tr(self.app, "f8"))
        first.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._compact_incoming(incoming)
        second, outgoing = card(grid, tr(self.app, "f9"), tone=AMBER)
        second.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        self._compact_outgoing(outgoing)
        third, overlay = card(grid, tr(self.app, "overlay_view"))
        third.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        self._compact_overlay(overlay)
        fourth, knowledge = card(grid, tr(self.app, "knowledge_state"), tone=AMBER)
        fourth.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        self._knowledge_card(knowledge)
        actions_frame, quick = card(content, tr(self.app, "quick"))
        actions_frame.pack(fill="x", padx=22, pady=(0, 16))
        for i, (name, cb) in enumerate((
            ("test", self.app.test_overlay),
            ("configure", self.app.toggle_overlay_edit),
            ("screenshot", self.app.capture_game_screenshot),
            ("update_knowledge", lambda: self.app._check_knowledge_update(True)),
        )):
            btn = action(quick, tr(self.app, name), cb)
            btn.pack(side="left", padx=(0, 8))
            if name == "configure": self.app.overlay_edit_button = btn

    def _server_card(self, parent):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x")
        try:
            from app import resource_path
            image = tk.PhotoImage(file=str(resource_path(FEATURED_SERVER.logo_asset)))
            self.app._featured_server_logo = image
            tk.Label(row, image=image, bg="#E6EEF1").pack(side="left", padx=(0, 14))
        except Exception:
            text(row, "CoD2", size=16, color=AMBER, bold=True).pack(side="left", padx=(0, 14))
        details = tk.Frame(row, bg=CARD)
        details.pack(side="left", fill="x", expand=True)
        text(details, FEATURED_SERVER.name, size=13, bold=True).pack(anchor="w")
        text(details, FEATURED_SERVER.subtitle, color=MUTED, size=9).pack(anchor="w", pady=(4, 0))
        text(details, FEATURED_SERVER.address, color=AMBER, size=10, bold=True).pack(anchor="w", pady=(5, 0))
        info = tk.Frame(parent, bg=CARD)
        info.pack(fill="x", pady=(10, 0))
        text(info, tr(self.app, "profile")+": ", color=MUTED, size=9).pack(side="left")
        tk.Label(info, textvariable=self.server_var, bg=CARD, fg=CYAN,
                 font=(FONT, 9, "bold")).pack(side="left")
        controls = tk.Frame(parent, bg=CARD)
        controls.pack(fill="x", pady=(11, 0))
        action(controls, tr(self.app, "connect"), self.app._launch_featured_server, primary=True).pack(side="left")
        discord = action(controls, "Discord", self.app._open_featured_server_discord)
        discord.pack(side="left", padx=(9, 0))
        if not FEATURED_SERVER.discord_url: discord.state(["disabled"])
        action(controls, tr(self.app, "server_settings"), self.app.show_server_settings).pack(side="left", padx=(9, 0))

    def _engine_card(self, parent):
        top = tk.Frame(parent, bg=CARD)
        top.pack(fill="x")
        text(top, "V2", size=22, color=CYAN, bold=True).pack(side="left", padx=(0, 15))
        tk.Label(top, textvariable=self.engine_var, bg=CARD, fg=GREEN,
                 font=(FONT, 12, "bold"), anchor="w").pack(side="left")
        tk.Label(parent, textvariable=self.base_var, bg=CARD, fg=TEXT,
                 font=(FONT, 10), anchor="w").pack(anchor="w", pady=(7, 0))
        text(parent, "Google / MyMemory  ·  "+tr(self.app, "online_hint"),
             size=9, color=MUTED).pack(anchor="w", pady=(5, 0))
        action(parent, tr(self.app, "learn"), lambda:self.navigate("knowledge")).pack(anchor="w", pady=(10, 0))

    def _compact_incoming(self, parent):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x")
        check(row, tr(self.app, "smart_enabled"), self.app.smart_engine_var, self.app._persist_settings).pack(side="left", padx=(0, 13))
        check(row, tr(self.app, "slang"), self.app.slang_var, self.app._persist_settings).pack(side="left", padx=(0, 13))
        check(row, tr(self.app, "dedupe"), self.app.dedupe_var, self.app._persist_settings).pack(side="left")
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=(9, 0))
        text(row, tr(self.app, "target")+": ", color=MUTED).pack(side="left")
        label = tk.Label(row, textvariable=self.app.target_name_var, bg=CARD, fg=CYAN, font=(FONT, 11, "bold"))
        label.pack(side="left")
        action(row, tr(self.app, "translation"), lambda:self.navigate("translation")).pack(side="right")
        tk.Label(parent, textvariable=self.metrics_var, fg=MUTED, bg=CARD,
                 font=(FONT, 9), anchor="w").pack(anchor="w", pady=(8, 0))

    def _compact_outgoing(self, parent):
        check(parent, tr(self.app, "enabled"), self.app.outgoing_chat.enabled_var,
              self.app._outgoing_enabled_changed).pack(anchor="w")
        tk.Label(parent, textvariable=self.app.outgoing_chat.route_var, bg=CARD,
                 fg=CYAN, font=(FONT, 12, "bold")).pack(anchor="w", pady=(8, 0))
        text(parent, tr(self.app, "enter_hint"), color=MUTED, size=9).pack(anchor="w", pady=(4, 0))
        action(parent, tr(self.app, "translation"), lambda:self.navigate("translation")).pack(anchor="w", pady=(7, 0))

    def _compact_overlay(self, parent):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x")
        check(row, tr(self.app, "enabled"), self.app.enabled_var,
              self.app.toggle_enabled).pack(side="left")
        tk.Label(row, textvariable=self.app.overlay_hotkey_status_var, bg=CARD,
                 fg=CYAN, font=(FONT, 9)).pack(side="left", padx=(12, 0))
        row2 = tk.Frame(parent, bg=CARD)
        row2.pack(fill="x", pady=(12, 0))
        action(row2, tr(self.app, "test"), self.app.test_overlay).pack(side="left")
        action(row2, tr(self.app, "overlay"), lambda:self.navigate("overlay")).pack(side="left", padx=(9, 0))

    def _knowledge_card(self, parent):
        tk.Label(parent, textvariable=self.base_var, bg=CARD, fg=CYAN,
                 font=(FONT, 11, "bold"), anchor="w").pack(anchor="w")
        text(parent, tr(self.app, "privacy"), color=MUTED, size=9, wraplength=350).pack(anchor="w", pady=(7, 6))
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=(4, 0))
        action(row, tr(self.app, "learn"), lambda:self.navigate("knowledge")).pack(side="left")
        action(row, tr(self.app, "export"), self.app._export_knowledge).pack(side="left", padx=(7, 0))

    def _translation(self, page):
        from premium_translation import translation_canvas_page
        translation_canvas_page(self, page)

    def _overlay(self, page):
        from premium_pages import overlay_page
        overlay_page(self, page)

    def _knowledge(self, page):
        app = self.app
        content = self._scroll_page(page, tr(app, "knowledge"),
            tr(app, "privacy"))
        summary_border, summary = card(content, tr(app, "knowledge_state"), tone=AMBER)
        summary_border.pack(fill="x", padx=22, pady=(0, 14))
        tk.Label(summary, textvariable=self.base_var, bg=CARD, fg=CYAN,
                 font=(FONT, 17, "bold")).pack(anchor="w")
        text(summary, tr(app, "online_hint") + ": Google / MyMemory",
             color=MUTED).pack(anchor="w", pady=(5, 0))

        options_border, options = card(content, tr(app, "learn"))
        options_border.pack(fill="x", padx=22, pady=(0, 14))
        values = (
            ("knowledge_v2_enabled", True,
             {"ru":"Использовать базу V2", "uk":"Використовувати базу V2", "en":"Enable V2 knowledge"}),
            ("knowledge_auto_update", True,
             {"ru":"Проверять знания при запуске", "uk":"Перевіряти знання під час запуску", "en":"Check knowledge at startup"}),
            ("experience_collect", False,
             {"ru":"Локально собирать примеры для экспорта", "uk":"Збирати приклади локально для експорту", "en":"Collect local examples for export"}),
            ("experience_cache", False,
             {"ru":"Сохранять временный кэш (7 дней)", "uk":"Зберігати тимчасовий кеш (7 днів)", "en":"Keep temporary disk cache (7 days)"}),
        )
        self.knowledge_options = {}
        def changed():
            for name, value in self.knowledge_options.items():
                app.config[name] = bool(value.get())
            runtime = getattr(app, "_knowledge_runtime", None)
            if runtime is not None:
                runtime.enabled = app.config["knowledge_v2_enabled"]
            app.experience.set_options(app.config["experience_collect"],
                                       app.config["experience_cache"])
            app._persist_settings()
            self.refresh()
        for name, fallback, captions in values:
            variable = tk.BooleanVar(master=self.root, value=bool(app.config.get(name, fallback)))
            self.knowledge_options[name] = variable
            check(options, captions.get(app.ui_language, captions["en"]), variable,
                  changed).pack(anchor="w", pady=(0, 4))
        note, privacy = card(content, tr(app, "privacy"), tone=AMBER)
        note.pack(fill="x", padx=22, pady=(0, 14))
        description = {
            "ru":"Тексты остаются на вашем ПК до ручного экспорта ZIP. Перед передачей проверьте архив: даже после фильтрации свободный текст может содержать личные данные.",
            "uk":"Тексти залишаються на ПК до ручного експорту ZIP. Перед передаванням перевірте архів: текст може містити особисті дані.",
            "en":"Examples remain on this PC until manual ZIP export. Review each archive before sharing: free text may still contain personal information.",
        }
        text(privacy, description.get(app.ui_language,description["en"]),
             color=MUTED, wraplength=780).pack(anchor="w")
        actions_border, actions = card(content, tr(app, "quick"))
        actions_border.pack(fill="x", padx=22, pady=(0, 16))
        for key, fn in (
            ("update_knowledge", lambda:app._check_knowledge_update(True)),
            ("export", app._export_knowledge),
            ("stats", lambda:self.navigate("stats")),
        ):
            action(actions, tr(app,key), fn).pack(side="left", padx=(0, 9))
        remove = {
            "ru":"Очистить локальный опыт", "uk":"Очистити локальний досвід",
            "en":"Clear local experience"
        }
        action(actions, remove.get(app.ui_language, remove["en"]),
               app._clear_knowledge, warm=True).pack(side="left")

    def _stats(self, page):
        content = self._scroll_page(page, tr(self.app, "stats"),
            tr(self.app, "actual"))
        live_border, live = card(content, tr(self.app, "latency"))
        live_border.pack(fill="x", padx=22, pady=(0, 14))
        tk.Label(live, textvariable=self.metrics_var, bg=CARD, fg=CYAN,
                 font=(FONT, 14, "bold")).pack(anchor="w")
        text(live, "p50 / p95  ·  Google / MyMemory  ·  "
             + tr(self.app, "online_hint"),
             color=MUTED).pack(anchor="w", pady=(6, 0))
        disk_border, disk = card(content, tr(self.app, "stats") + " · ZIP", tone=AMBER)
        disk_border.pack(fill="x", padx=22, pady=(0, 14))
        self.disk_stats_var = tk.StringVar(master=self.root,
                                          value=tr(self.app, "no_samples"))
        tk.Label(disk, textvariable=self.disk_stats_var, bg=CARD, fg=TEXT,
                 font=(FONT, 10), anchor="w", justify="left",
                 wraplength=750).pack(fill="x")
        actions_border, actions = card(content, tr(self.app, "quick"))
        actions_border.pack(fill="x", padx=22, pady=(0, 16))
        refresh_text = {
            "ru":"Обновить измерения", "uk":"Оновити вимірювання",
            "en":"Refresh measurements"
        }
        action(actions, refresh_text.get(self.app.ui_language, refresh_text["en"]),
               self.request_stats, primary=True).pack(side="left")
        action(actions, tr(self.app, "export"), self.app._export_knowledge).pack(side="left", padx=9)

    def request_stats(self):
        app = self.app
        if not app.experience.stats(
            lambda ok, data: app.ui_queue.put(("dashboard_stats", ok, data))
        ):
            self.disk_stats_var.set("Database busy")

    def update_stats(self, ok, data):
        if not hasattr(self, "disk_stats_var"): return
        if not ok:
            self.disk_stats_var.set(str(data))
            return
        groups = data[2]
        lines = [f"{tr(self.app, 'base')}: {data[0]}  ·  samples: {data[1]}"]
        for direction in ("incoming", "outgoing", "ui"):
            stats = groups.get(direction)
            if stats:
                name = {"incoming":"F8","outgoing":"F9","ui":"UI"}[direction]
                lines.append(f"{name}: {stats['samples']} samples  ·  "
                             f"p50 {stats['p50_ms']} ms  ·  "
                             f"p95 {stats['p95_ms']} ms  ·  errors: {stats['failed']}")
        self.disk_stats_var.set("\n".join(lines))
    def _settings(self, page):
        content = self._scroll_page(page, tr(self.app, "settings_head"), tr(self.app, "settings_sub"))
        server_border, server = card(content, tr(self.app, "profile"))
        server_border.pack(fill="x", padx=22, pady=(0, 14))
        tk.Label(server, textvariable=self.server_var, fg=CYAN, bg=CARD,
                 font=(FONT, 11, "bold")).pack(anchor="w")
        action(server, tr(self.app, "server_settings"), self.app.show_server_settings,
               primary=True).pack(anchor="w", pady=(12, 0))
        language_border, language = card(content, tr(self.app, "interface"), tone=AMBER)
        language_border.pack(fill="x", padx=22, pady=(0, 14))
        languages, _ = label_combo(language, tr(self.app, "interface"),
            ["Русский", "Українська", "English"],
            self.app.ui_language_var, lambda _e:self.app.change_ui_language(), width=18)
        languages.pack(anchor="w")
        maint_border, maint = card(content, tr(self.app, "quick"))
        maint_border.pack(fill="x", padx=22, pady=(0, 16))
        for name, fn in (
            ("updates", lambda:self.app.check_updates(manual=True)),
            ("cod2", self.app.enable_cod2_borderless),
            ("learn", lambda:self.navigate("knowledge")),
            ("about", self.app.show_about),
        ):
            action(maint, tr(self.app, name), fn).pack(side="left", padx=(0, 8))

    def navigate(self, name):
        if name not in self.pages:
            return False
        self.page = name
        self.pages[name].tkraise()
        if name == "stats":
            self.request_stats()
        for key, button in self.nav_buttons.items():
            selected = key == name
            button.configure(bg="#164052" if selected else SIDEBAR,
                             fg=CYAN if selected else MUTED,
                             font=(FONT, 11, "bold" if selected else "normal"))
        return True

    def refresh(self):
        app = self.app
        if not self.outer.winfo_exists():
            return
        from knowledge_v2 import version as knowledge_version
        kb = knowledge_version()
        if not app.smart_engine_var.get():
            engine = "Classic"
        elif kb:
            engine = "Smart V2"
        else:
            engine = "Smart V1"
        self.engine_var.set(engine)
        self.active_var.set(tr(app, "app_active") if app.enabled_var.get() else app.t("translator_off_status"))
        runtime = app._knowledge_runtime
        if kb and runtime:
            self.base_var.set(f"v{runtime.version}  ·  {runtime.pack.count} {tr(app, 'base').lower()}")
        else:
            self.base_var.set("Smart V1 / Classic  ·  "+tr(app, "knowledge_state"))
        shared = getattr(app, "translation_shared_state", None)
        if shared:
            stats = shared.snapshot()
            if stats["samples"]:
                self.metrics_var.set(
                    f"F8 · p50 {stats['provider_p50_ms']:.0f} ms · "
                    f"p95 {stats['provider_p95_ms']:.0f} ms "
                    f"· n={stats['samples']}"
                )
            else:
                self.metrics_var.set(tr(app, "no_samples"))
        else:
            self.metrics_var.set(tr(app, "no_samples"))
        self.footer_engine.configure(text=engine)

    def _tick(self):
        try:
            if not self.outer.winfo_exists():
                return
            self.refresh()
            self.root.after(1500, self._tick)
        except tk.TclError:
            return


def build_dashboard(app):
    # Statically inspectable alias surface. Real app variables keep the
    # translations/backends intact and original GUI actions remain callable.
    app._update_overlay_hotkey_status()
    app.dashboard = Dashboard(app)
