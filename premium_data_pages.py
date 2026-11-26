"""Knowledge, statistics and settings arranged as four subject-focused instruments."""
from __future__ import annotations
import tkinter as tk
from dashboard_ui import BG, CARD, TEXT, MUTED, AMBER, CYAN, FONT, tr, text, card, check, action, label_combo


def _board(dashboard, page, title, subtitle):
    content = dashboard._scroll_page(page, title, subtitle)
    board = tk.Frame(content, bg=BG)
    board.pack(fill="both", expand=True, padx=15, pady=(0, 12))
    board.columnconfigure(0, weight=1, uniform="expert")
    board.columnconfigure(1, weight=1, uniform="expert")
    board.rowconfigure(0, weight=1)
    board.rowconfigure(1, weight=1)
    return board


def _section(board, row, column, title):
    border, body = card(board, title)
    border.grid(row=row, column=column, sticky="nsew",
                padx=(0, 5) if column == 0 else (5, 0), pady=(0, 10))
    return body


def knowledge_page(dashboard, page):
    app = dashboard.app
    board = _board(dashboard, page, tr(app, "knowledge"), tr(app, "privacy"))
    lang = app.ui_language
    titles = {
        "ru": ("СОСТОЯНИЕ", "ОБНОВЛЕНИЯ", "ЛОКАЛЬНЫЙ ОПЫТ", "ДАННЫЕ И ОБСЛУЖИВАНИЕ"),
        "uk": ("СТАН", "ОНОВЛЕННЯ", "ЛОКАЛЬНИЙ ДОСВІД", "ДАНІ ТА ОБСЛУГОВУВАННЯ"),
        "en": ("STATUS", "UPDATES", "LOCAL EXPERIENCE", "DATA AND MAINTENANCE"),
    }[lang]
    state = _section(board, 0, 0, titles[0])
    updates = _section(board, 0, 1, titles[1])
    local = _section(board, 1, 0, titles[2])
    data = _section(board, 1, 1, titles[3])
    tk.Label(state, textvariable=dashboard.base_var, bg=CARD, fg=AMBER,
             font=(FONT, 16, "bold"), anchor="w").pack(anchor="w", pady=(6, 12))
    dashboard.knowledge_options = {}
    entries = (
        ("knowledge_v2_enabled", True, state,
         {"ru":"Использовать базу V2","uk":"Використовувати базу V2","en":"Enable V2 knowledge"}),
        ("knowledge_auto_update", True, updates,
         {"ru":"Проверять при запуске","uk":"Перевіряти під час запуску","en":"Check at startup"}),
        ("experience_collect", False, local,
         {"ru":"Локально собирать примеры для экспорта","uk":"Збирати приклади локально для експорту","en":"Collect local examples for export"}),
        ("experience_cache", False, local,
         {"ru":"Сохранять временный кэш (7 дней)","uk":"Зберігати тимчасовий кеш (7 днів)","en":"Keep temporary cache (7 days)"}),
    )
    def changed():
        for name, value in dashboard.knowledge_options.items():
            app.config[name] = bool(value.get())
        runtime = getattr(app, "_knowledge_runtime", None)
        if runtime is not None:
            runtime.enabled = app.config["knowledge_v2_enabled"]
        app.experience.set_options(app.config["experience_collect"],
                                   app.config["experience_cache"])
        app._persist_settings()
        dashboard.refresh()
    for name, default, parent, captions in entries:
        variable = tk.BooleanVar(master=dashboard.root,
                                  value=bool(app.config.get(name, default)))
        dashboard.knowledge_options[name] = variable
        check(parent, captions[lang], variable, changed).pack(anchor="w", pady=2)
    action(updates, tr(app, "update_knowledge"),
           lambda:app._check_knowledge_update(True), primary=True).pack(
               anchor="w", pady=(10, 0))
    text(local, {"ru":"Примеры остаются на этом ПК до ручного экспорта.",
                 "uk":"Приклади залишаються на цьому ПК до ручного експорту.",
                 "en":"Examples remain on this PC until manual export."}[lang],
         color=MUTED, wraplength=480).pack(anchor="w", pady=(10, 0))
    action(data, tr(app, "export"), app._export_knowledge).pack(anchor="w", pady=(4, 8))
    clear = {"ru":"Очистить локальный опыт…","uk":"Очистити локальний досвід…",
             "en":"Clear local experience…"}[lang]
    action(data, clear, app._clear_knowledge, warm=True).pack(anchor="w")
    text(data, {"ru":"Удаление требует отдельного подтверждения.",
                "uk":"Видалення потребує окремого підтвердження.",
                "en":"Clearing requires a separate confirmation."}[lang],
         color=MUTED, wraplength=480).pack(anchor="w", pady=(9, 0))


def stats_page(dashboard, page):
    app = dashboard.app
    board = _board(dashboard, page, tr(app, "stats"), tr(app, "actual"))
    heading = {"ru":("ВХОДЯЩИЙ ПЕРЕВОД · F8", "ЛОКАЛЬНЫЙ ОПЫТ · F8/F9"),
               "uk":("ВХІДНИЙ ПЕРЕКЛАД · F8", "ЛОКАЛЬНИЙ ДОСВІД · F8/F9"),
               "en":("INCOMING TRANSLATION · F8", "LOCAL EXPERIENCE · F8/F9")}[app.ui_language]
    incoming = _section(board, 0, 0, heading[0])
    local = _section(board, 0, 1, heading[1])
    tk.Label(incoming, textvariable=dashboard.metrics_var, bg=CARD, fg=AMBER,
             font=(FONT, 14, "bold"), anchor="w").pack(anchor="w", pady=(8, 12))
    text(incoming, {"ru":"Измерения появятся после реальных переводов.",
                    "uk":"Вимірювання з’являться після реальних перекладів.",
                    "en":"Measurements appear after actual translations."}[app.ui_language],
         color=MUTED, wraplength=470).pack(anchor="w")
    dashboard.disk_stats_var = tk.StringVar(master=dashboard.root,
                                            value=tr(app, "no_samples"))
    tk.Label(local, textvariable=dashboard.disk_stats_var, bg=CARD, fg=TEXT,
             font=(FONT, 11), anchor="w", justify="left",
             wraplength=470).pack(fill="x", pady=(8, 8))
    refresh = {"ru":"Обновить измерения", "uk":"Оновити вимірювання",
               "en":"Refresh measurements"}[app.ui_language]
    action(local, refresh, dashboard.request_stats, primary=True).pack(anchor="w")
    # No made-up counters and no duplicated knowledge export action.


def settings_page(dashboard, page):
    app = dashboard.app
    board = _board(dashboard, page, tr(app, "settings_head"),
                   tr(app, "settings_sub"))
    titles = {
        "ru":("ИГРА И СЕРВЕР", "ЯЗЫК И ОТОБРАЖЕНИЕ", "СИСТЕМА", "О ПРОГРАММЕ"),
        "uk":("ГРА І СЕРВЕР", "МОВА І ВІДОБРАЖЕННЯ", "СИСТЕМА", "ПРО ПРОГРАМУ"),
        "en":("GAME AND SERVER", "LANGUAGE AND DISPLAY", "SYSTEM", "ABOUT"),
    }[app.ui_language]
    game = _section(board, 0, 0, titles[0])
    appearance = _section(board, 0, 1, titles[1])
    system = _section(board, 1, 0, titles[2])
    about = _section(board, 1, 1, titles[3])
    tk.Label(game, textvariable=dashboard.server_var, bg=CARD, fg=AMBER,
             font=(FONT, 12, "bold"), anchor="w").pack(anchor="w", pady=(5, 10))
    action(game, tr(app, "server_settings"), app.show_server_settings,
           primary=True).pack(anchor="w")
    languages, _ = label_combo(appearance, tr(app, "interface"),
        ["Русский", "Українська", "English"], app.ui_language_var,
        lambda _e:app.change_ui_language(), width=18)
    languages.pack(anchor="w", pady=(5, 0))
    for key, fn in (("updates", lambda:app.check_updates(manual=True)),
                    ("cod2", app.enable_cod2_borderless)):
        action(system, tr(app, key), fn).pack(anchor="w", pady=(5, 5))
    action(about, tr(app, "about"), app.show_about).pack(anchor="w", pady=(5, 5))
    text(about, {"ru":"Версия и сведения о программе",
                 "uk":"Версія та відомості про програму",
                 "en":"Version and application information"}[app.ui_language],
         color=MUTED).pack(anchor="w", pady=(7, 0))
