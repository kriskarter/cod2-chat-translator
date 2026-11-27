"""Working translation services with no Tk event loop or Tk widgets.

The existing application's algorithms are reused exactly. This development
runtime is opt-in, reads the supplied configuration, and never writes it.
"""
from __future__ import annotations

import json
from copy import deepcopy
import os
import queue
import threading
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QTimer, Signal, Slot, Property, Qt
from app import (ControlApp, DEFAULT_CONFIG, UI_STRINGS, TARGET_LANGUAGES,
                 SLANG_STYLES, LogTailer, TranslatorWorker,
                 TranslationWorkerSharedState, RecentDuplicateFilter,
                 deep_merge, gaming_slang_transform, merge_server_profiles,
                 discover_cod2_logs, choose_active_log_from_activity, activity_snapshot, APP_VERSION, _path_key)
from outgoing_chat import (OutgoingTranslationDispatcher, OutgoingHttpTransport,
                           translate_outgoing_text, LANGUAGES as OUTGOING_LANGUAGES)
import knowledge_v2
import translation_memory
from .live_monitor import LiveMonitorState
from .friend_presence import qt_monitor_settings, dump_qt_monitor_settings, display_name
from .common import ROOT
from .admin_policy import admin_policy, VERSION_KEY, ADMIN_POLICY_VERSION
from .native_hud import NativeHud
from .outgoing_hud import outgoing_config, positioned, render_editor
from server_monitor import load_settings, dump_settings


def read_translation_config(path: Path | None):
    if path is None:
        return deep_merge(DEFAULT_CONFIG, {})
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration root must be an object")
    return deep_merge(DEFAULT_CONFIG, raw)


HUD_PRESETS = {"text": (420, 120, 9, 0.), "minimal": (420, 120, 9, .15), "readable": (500, 150, 10, .12)}

class TranslationState(LiveMonitorState):
    shortcutWake = Signal()
    feedback = Signal(str, str, bool)
    translationChanged = Signal()
    # These existing methods access only the ingress contract below, not Tk.
    # Keeping one algorithm preserves deduplication, context and local fast path.
    on_log_message = ControlApp.on_log_message
    _on_log_control = ControlApp._on_log_control

    def __init__(self, config, game_exe=None, log_path=None, installed_knowledge=None, game_hotkeys=False, settings_store=None):
        config = admin_policy(config)
        super().__init__(qt_monitor_settings(config.get("server_monitor")), game_exe)
        self._config = config
        self._store = settings_store
        self._outgoing_hud_config = outgoing_config(config.get("outgoing_hud"))
        self._last_outgoing_rect = None
        self._privilege_mismatch = False
        self._startup_elevation_denied = False
        self._always_admin = config.get("qt_always_admin") is True
        self._history_enabled = config.get("qt_history_enabled", True)
        self._hint_dismissed = bool(config.get("qt_hint_dismissed", False))
        self._game_running = False
        self._privilege_timer = QTimer(self)
        self._privilege_timer.setInterval(2500)
        self._privilege_timer.timeout.connect(self._check_game_privileges)
        self._profiles = merge_server_profiles(config.get("server_profiles"), [])
        self._auto_profile = bool(config.get("auto_detect_profile", True))
        self._profile_activity = {}
        self._pending_switch_positions = {}
        self._last_profile_scan = time.monotonic()
        self._notifications = deque(maxlen=80)
        self._notice_window = None
        self._last_friend_sound_at = -1e9
        self._maintenance_busy = False
        self._update_message = ""
        self._update_url = ""
        self._update_candidate = None
        self._update_package = None
        self._update_cancel = threading.Event()
        self._knowledge_writable = installed_knowledge is not None and Path(installed_knowledge).resolve() != (ROOT / "assets" / "knowledge_v2.json").resolve()
        self._profile_timer = QTimer(self)
        self._profile_timer.setInterval(2500)
        self._profile_timer.timeout.connect(self._poll_profiles)
        self.ui_language = config.get("ui_language", "ru")
        if self.ui_language not in ("ru", "uk", "en"): self.ui_language = "ru"
        self._translation_status = self.trText("Ожидание запуска")
        self._history = deque(maxlen=200)
        self._outgoing_result = ""
        self._outgoing_busy = False
        self._outgoing_id = 0
        self._f8 = self.enabled = bool(config.get("qt_f8_enabled", True))
        self._f9 = bool(config.get("outgoing_enabled", True))
        self._out_source = config.get("outgoing_source_language", self.ui_language)
        self._out_target = config.get("outgoing_target_language", "en")
        if self._out_source not in OUTGOING_LANGUAGES.values(): self._out_source = "ru"
        if self._out_target not in OUTGOING_LANGUAGES.values(): self._out_target = "en"
        self._smart = bool(config.get("smart_engine_enabled", True))
        self._target = config.get("target_language", "ru")
        if self._target not in TARGET_LANGUAGES.values():
            self._target = "ru"
        self._style = config.get("slang_style", "live")
        if self._style not in SLANG_STYLES.values():
            self._style = "live"
        self._hide = bool(config.get("hide_same_language", True))
        self._slang = bool(config.get("gaming_slang", True))
        self._dedupe = bool(config.get("deduplicate_messages", True))
        self._update_settings()
        raw_log = log_path or config.get("active_profile_path") or config.get("log_path")
        self._log_path = Path(raw_log).expanduser().resolve() if raw_log else None
        if self._log_path:
            self._profiles = merge_server_profiles(self._profiles, [self._log_path])
        self._profile_activity = activity_snapshot([Path(r["path"]) for r in self._profiles])
        self._resolve_game_exe()
        self.stop_event = threading.Event()
        self.translation_jobs = queue.Queue(maxsize=50)
        self.ui_queue = queue.Queue()
        self.duplicate_filter = RecentDuplicateFilter(float(config.get("duplicate_window_seconds", 4)))
        self._arrival_context = deque(maxlen=24)
        self._chat_epoch = 0
        self._shortcut_notice = NativeHud(dict(config.get("overlay", {}), message_ttl_seconds=2, max_messages=1, background_only_with_messages=True))
        self._hud = NativeHud(config.get("overlay", {}), config.get("show_original", False))
        self._overlay_on_start = bool(config.get("qt_overlay_enabled", True))
        self._notifier = None
        self._experience = None
        self._previous_experience = translation_memory.RUNTIME
        self._experience_stats = []
        self._observation_count = 0
        self._knowledge_previous = knowledge_v2.RUNTIME
        bundled = ROOT / "assets" / "knowledge_v2.json"
        runtime = knowledge_v2.KnowledgeRuntime(bundled, installed_knowledge or bundled)
        runtime.enabled = bool(config.get("knowledge_v2_enabled", True))
        knowledge_v2.configure(runtime)
        if self._store:
            self._experience = translation_memory.LocalExperience(
                self._store.path.parent / "translation_experience.sqlite3",
                collect=bool(config.get("experience_collect", False)),
                cache=bool(config.get("experience_cache", False)))
            translation_memory.configure(self._experience)
            if self._experience.cache: self._experience.set_options(self._experience.collect, True)
        self._shared = TranslationWorkerSharedState()
        self._workers = [TranslatorWorker(
            jobs=self.translation_jobs, ui_queue=self.ui_queue,
            target_getter=lambda: self._f8_settings[0],
            hide_same_getter=lambda: self._f8_settings[1],
            slang_enabled_getter=lambda: self._f8_settings[2],
            slang_style_getter=lambda: self._f8_settings[3],
            smart_enabled_getter=lambda: self._f8_settings[4],
            stop_event=self.stop_event, shared_state=self._shared)
            for _ in range(2)]
        self._tailer = LogTailer(lambda: self._log_path, self.on_log_message,
                                lambda s: self.ui_queue.put(("status", s)),
                                self.stop_event, self._on_log_control, self.t,
                                switch_position_getter=self._consume_switch_position)
        self._transport = OutgoingHttpTransport()
        self._dispatcher = OutgoingTranslationDispatcher(
            self._translate_outgoing, on_worker_exit=self._transport.close_current_thread)
        self._timer = QTimer(self)
        self._timer.setInterval(80 if game_hotkeys else 120)
        self._timer.timeout.connect(self._drain)
        self._started = False
        self._game = None
        self._screenshot_in_progress = False
        if game_hotkeys and os.name == "nt":
            from .game_controls import GameControls
            self.shortcutWake.connect(self._drain, Qt.QueuedConnection)
            self._game = GameControls(self, self._outgoing_hud_config,
                                      self._out_source, self._out_target)

    _screenshot_directory = ControlApp._screenshot_directory
    _screenshot_status = ControlApp._screenshot_status
    def _capture_game_screenshot_worker(self):
        # Never fall back to capturing a different application or whole desktop.
        import time
        from PIL import ImageGrab
        from outgoing_send import _foreground_api, is_cod2_foreground
        try:
            user, _ = _foreground_api()
            hwnd = user.GetForegroundWindow()
            if not hwnd or not is_cod2_foreground() or hwnd != user.GetForegroundWindow():
                raise RuntimeError("CoD2 не в фокусе")
            image = ImageGrab.grab(window=hwnd)
            if hwnd != user.GetForegroundWindow() or not is_cod2_foreground():
                raise RuntimeError("Фокус CoD2 потерян")
            if not image.width or not image.height or image.getbbox() is None:
                raise RuntimeError("Окно CoD2 недоступно")
            path = self._screenshot_directory() / f"CoD2_Chat_Translator_{time.strftime('%Y-%m-%d_%H-%M-%S')}_{time.time_ns()%1000000000:09d}.png"
            image.save(path, format="PNG")
            self.ui_queue.put(("screenshot_saved", str(path)))
        except Exception as error:
            self.ui_queue.put(("screenshot_error", str(error)))
        finally:
            self._screenshot_in_progress = False

    def show_f8_notice(self):
        notice = self._shortcut_notice
        notice.config.update(x=self._hud.config.get("x",8), y=self._hud.config.get("y",360))
        if notice.enable(True):
            notice.add("F8", "", self.trText("Входящий перевод включён" if self._f8 else "Входящий перевод выключен"))

    def game_status(self, text):
        self._translation_status = self.trText(text)
        self.translationChanged.emit()

    def capture_game_screenshot(self):
        if os.name != "nt" or self._screenshot_in_progress:
            return
        self._screenshot_in_progress = True
        self.game_status(self._screenshot_status("capturing"))
        threading.Thread(target=self._capture_game_screenshot_worker, daemon=True,
                         name="QtCoD2Screenshot").start()


    def t(self, key):
        return UI_STRINGS.get(self.ui_language, UI_STRINGS["ru"]).get(key, key)

    def _update_settings(self):
        self._f8_settings = (self._target, self._hide, self._slang,
                             self._style, self._smart, self._dedupe)

    @Property(bool, constant=True)
    def settingsWritable(self): return self._store is not None

    @Slot()
    def saveSettings(self):
        if self._store is None:
            return
        config = dict(self._config)
        config[VERSION_KEY] = max(ADMIN_POLICY_VERSION, config.get(VERSION_KEY, ADMIN_POLICY_VERSION))
        config.update(target_language=self._target, smart_engine_enabled=self._smart,
                      qt_f8_enabled=self._f8, qt_overlay_enabled=self._overlay_on_start,
                      qt_always_admin=self._always_admin, qt_history_enabled=self._history_enabled, qt_hint_dismissed=self._hint_dismissed, outgoing_enabled=self._f9,
                      outgoing_source_language=self._out_source, outgoing_target_language=self._out_target,
                      log_path=str(self._log_path or ""), active_profile_path=str(self._log_path or ""),
                      server_monitor=dump_qt_monitor_settings(self._settings), ui_language=self.ui_language,
                      server_profiles=self._profiles, auto_detect_profile=self._auto_profile,
                      knowledge_v2_enabled=knowledge_v2.RUNTIME.enabled,
                      hide_same_language=self._hide, gaming_slang=self._slang,
                      deduplicate_messages=self._dedupe, slang_style=self._style,
                      show_original=self._hud.show_original, overlay=dict(self._hud.config),
                      outgoing_hud=dict(self._outgoing_hud_config),
                      experience_collect=bool(self._experience and self._experience.collect),
                      experience_cache=bool(self._experience and self._experience.cache))
        try:
            self._store.save(config)
            self._config = config
            self.game_status("Настройки сохранены")
            self.feedback.emit("", self.translationStatus, False)
            return True
        except (OSError, RuntimeError) as error:
            self.game_status(self.trText("Ошибка сохранения") + ": " + str(error))
            self.feedback.emit("", self.translationStatus, True)
            return False

    def _persist_servers(self, servers):
        if self._store is None:
            return True
        # Commit only the explicit server mutation, before changing the UI or
        # monitor. Keep unrelated preferences and unknown configuration keys.
        try:
            config = deepcopy(self._store.load(self._config))
            monitor = config.get("server_monitor")
            monitor = dict(monitor) if isinstance(monitor, dict) else {}
            monitor["servers"] = [vars(server).copy() for server in servers]
            config["server_monitor"] = monitor
            self._store.save(config)
            self._config = config
            return True
        except (OSError, RuntimeError, ValueError) as error:
            self._server_error = self.trText("Ошибка сохранения") + ": " + str(error)
            self.game_status(self._server_error)
            self.feedback.emit("", self._server_error, True)
            return False

    def _save_friend_settings(self):
        if self._store is None: return True
        # Auto-save only explicit friend mutations/preferences, not unrelated
        # unsaved edits or network callbacks. Keep the legacy import read-only.
        try:
            config=deepcopy(self._store.load(self._config))
            monitor=config.get("server_monitor")
            monitor=dict(monitor) if isinstance(monitor,dict) else {}
            for key in ("friends","notify_friends","notify_join","notify_leave","notify_move","notify_sound"):
                monitor[key]=deepcopy(self._settings[key])
            config["server_monitor"]=monitor
            self._store.save(config)
            self._config=config
            return True
        except (OSError,RuntimeError,ValueError) as error:
            self._friend_error=self.trText("Ошибка сохранения")+": "+str(error)
            self.game_status(self._friend_error)
            self.friendNotice.emit(self.trText("Ошибка сохранения"),str(error))
            return False

    @Property(str, notify=translationChanged)
    def uiLanguage(self): return self.ui_language

    @Slot(str)
    def setUiLanguage(self, code):
        if code in ("ru", "uk", "en") and code != self.ui_language:
            self.ui_language = code
            if self._store is not None:
                try:
                    saved=deepcopy(self._store.load(self._config));saved["ui_language"]=code;self._store.save(saved);self._config=saved
                except (OSError,RuntimeError,ValueError) as error: self.game_status(self.trText("Ошибка сохранения")+": "+str(error))
            self.translationChanged.emit()
            self.rowsChanged.emit()
            self.changed.emit()

    @Property('QVariantList', notify=translationChanged)
    def profiles(self): return list(self._profiles)

    @Property(bool, notify=translationChanged)
    def autoProfile(self): return self._auto_profile

    @Slot(bool)
    def setAutoProfile(self, enabled):
        self._auto_profile = enabled
        self._profile_activity = activity_snapshot([Path(r["path"]) for r in self._profiles])
        self.translationChanged.emit()

    @Slot(str, str, result=bool)
    def renameProfile(self, path, name):
        name = name.strip()[:80]
        if not name: return False
        for record in self._profiles:
            if record["path"] == path:
                record["name"] = name
                self.translationChanged.emit()
                return True
        return False

    @Slot()
    def rescanProfiles(self):
        if self._maintenance_busy: return
        self._maintenance_busy = True
        self._last_profile_scan = time.monotonic()
        self.translationChanged.emit()
        roots = list(self._config.get("cod2_roots") or [])
        def worker():
            try: self.ui_queue.put(("qt_maintenance", "profiles", discover_cod2_logs(roots), ""))
            except Exception as e: self.ui_queue.put(("qt_maintenance", "profiles", [], str(e)))
        threading.Thread(target=worker, daemon=True, name="QtProfileScan").start()

    @Slot()
    def enableGameLogging(self):
        if self._maintenance_busy: return
        self._maintenance_busy = True
        self.translationChanged.emit()
        roots = list(self._config.get("cod2_roots") or [])
        def worker():
            try:
                from app import discover_cod2_game_roots, discover_running_cod2_roots, ensure_cod2_console_logging
                roots_found = discover_cod2_game_roots(roots)
                summary = ensure_cod2_console_logging(roots_found, running_roots=discover_running_cod2_roots())
                self.ui_queue.put(("qt_maintenance", "logging", summary, ""))
            except Exception as error:
                self.ui_queue.put(("qt_maintenance", "logging", None, str(error)))
        threading.Thread(target=worker, daemon=True, name="QtEnableGameLogging").start()

    def _resolve_game_exe(self):
        if os.name != "nt" or self._game_exe: return
        from app import infer_cod2_root
        from server_catalog import find_multiplayer_executable
        roots = [*self._config.get("cod2_roots", []), *(infer_cod2_root(r["path"]) for r in self._profiles)]
        self._game_exe = find_multiplayer_executable(roots)
        self._can_connect = self._game_exe is not None
        self.changed.emit()

    def _consume_switch_position(self, path):
        return self._pending_switch_positions.pop(_path_key(path), None)

    def _poll_profiles(self):
        if not self._auto_profile: return
        if self._started and not self._maintenance_busy and time.monotonic() - self._last_profile_scan > 45:
            self.rescanProfiles()
        if not self._profiles: return
        previous = self._profile_activity
        chosen, self._profile_activity = choose_active_log_from_activity(
            [Path(r["path"]) for r in self._profiles], self._profile_activity, self._log_path)
        if chosen:
            before = previous.get(_path_key(chosen))
            current = self._profile_activity.get(_path_key(chosen))
            self._pending_switch_positions[_path_key(chosen)] = before[1] if before and current and current[1] >= before[1] else 0
            self.setLogPath(str(chosen))

    @Property(bool, notify=translationChanged)
    def maintenanceBusy(self): return self._maintenance_busy

    @Property('QStringList', notify=translationChanged)
    def notifications(self): return list(self._notifications)

    @Property(bool, notify=translationChanged)
    def notifyFriends(self): return bool(self._settings["notify_friends"])

    @Slot(bool)
    def setNotifyFriends(self, enabled):
        self.setFriendNotification("friends",enabled)

    @Property("QVariantMap", notify=translationChanged)
    def friendNotificationOptions(self):
        return {key:bool(self._settings["notify_"+key]) for key in ("friends","join","leave","move","sound")}

    @Slot(str,bool,result=bool)
    def setFriendNotification(self,key,enabled):
        if key not in ("friends","join","leave","move","sound"): return False
        option="notify_"+key
        previous=self._settings[option]
        self._settings[option]=enabled
        self._friend_error=""
        if not self._save_friend_settings():
            self._settings[option]=previous
            self.friendsChanged.emit()
            self.translationChanged.emit()
            return False
        self.translationChanged.emit()
        self.friendsChanged.emit()
        return True

    def _on_presence_event(self,event):
        if not self.notifyFriends or not self._settings["notify_"+event.kind]: return
        labels={r.address:r.name for r in self._rows.values()}
        title=self.trText({"join":"Друг появился","leave":"Друг покинул сервер","move":"Возможный переход друга"}[event.kind])
        name=display_name(event.name)
        old=labels.get(event.old_address,event.old_address)
        new=labels.get(event.new_address,event.new_address)
        detail=name+" · "+(old+" → "+new if event.kind=="move" else new or old)
        server = self._rows.get(event.new_address or event.old_address)
        if server and server.map_name and server.map_name != "—":
            detail += " · " + server.map_name
        self._notifications.appendleft(title+": "+detail)
        # In-app notification is custom QML. When not active use native
        # notification delivery; its sound flag is controlled independently.
        active=bool(self._notice_window and self._notice_window.isActive())
        sound=bool(self._settings["notify_sound"])
        if active or not self._notifier or not self._notifier.show(title,detail,sound=False):
            self.friendNotice.emit(title,detail)
        now=time.monotonic()
        if sound and now-self._last_friend_sound_at>=2.5:
            self._last_friend_sound_at=now
            self._play_friend_sound()
        self.translationChanged.emit()

    @staticmethod
    def _play_friend_sound():
        if os.name != "nt": return
        try:
            import winsound
            winsound.PlaySound(str(ROOT/"assets"/"friend_notice.wav"),winsound.SND_FILENAME|winsound.SND_ASYNC|winsound.SND_NODEFAULT)
        except (RuntimeError,OSError): pass

    @Property('QVariantMap', notify=translationChanged)
    def preferences(self):
        return {"hide": self._hide, "slang": self._slang, "dedupe": self._dedupe,
                "original": self._hud.show_original, "style": self._style,
                "font": self._hud.config.get("font_size", 10),
                "ttl": self._hud.ttl,
                "opacity": self._hud.config.get("background_opacity", .15),
                "width": self._hud.config.get("width", 500), "height": self._hud.config.get("height", 150),
                "x": self._hud.config.get("x", 8), "y": self._hud.config.get("y", 360),
                "messages": self._hud.items.maxlen,
                "fade": self._hud.config.get("fade_enabled", True),
                "compact": self._hud.config.get("compact_background", True),
                "onlyMessages": self._hud.config.get("background_only_with_messages", True),
                "autoHeight": self._hud.config.get("auto_height", True)}

    @Slot(str, bool)
    def setPreference(self, key, value):
        if key == "original":
            self._hud.show_original = value
            self._hud._render()
        elif key in ("fade", "compact", "onlyMessages", "autoHeight"):
            self._hud.config[{"fade":"fade_enabled","compact":"compact_background","onlyMessages":"background_only_with_messages","autoHeight":"auto_height"}[key]] = value
            self._hud._render()
        elif key in ("hide", "slang", "dedupe"):
            setattr(self, "_" + key, value)
            self._update_settings()
            self._on_log_control("map_change", "settings_change")
            if self._game: self._game.cancel()
        else: return
        self.translationChanged.emit()

    @Slot(str)
    def setSlangStyle(self, style):
        if style in SLANG_STYLES.values():
            self._style = style
            self._update_settings()
            self._on_log_control("map_change", "settings_change")
            if self._game: self._game.cancel()
            self.translationChanged.emit()

    @Slot(str, float)
    def setHudValue(self, key, value):
        if key == "font":
            self._hud.config["font_size"] = max(8, min(20, int(value)))
        elif key == "ttl":
            self._hud.ttl = max(1, min(120, value))
            self._hud.config["message_ttl_seconds"] = self._hud.ttl
        elif key == "opacity":
            self._hud.config["background_opacity"] = max(0, min(.9, value))
        elif key in ("width", "height", "x", "y"):
            lo, hi = {"width":(200, 1200),"height":(46, 600),"x":(-6000, 6000),"y":(-6000, 6000)}[key]
            self._hud.config[key] = max(lo, min(hi, int(value)))
        elif key == "messages":
            self._hud.resize_buffer(max(1, min(10, int(value))))
        else: return
        self._hud._render()
        self.translationChanged.emit()

    @Property(str, notify=translationChanged)
    def hudPreset(self):
        prefs = self.preferences
        if not all(prefs[k] for k in ("onlyMessages", "compact", "fade", "autoHeight")) or prefs["messages"] != 4 or prefs["ttl"] != 10:
            return ""
        values = tuple(prefs[k] for k in ("width", "height", "font", "opacity"))
        return next((name for name, preset in HUD_PRESETS.items() if values == preset), "")

    @Slot(str)
    def applyHudPreset(self, preset):
        values = HUD_PRESETS.get(preset)
        if values is None: return
        w,h,font,opacity = values
        self._hud.config.update(width=w,height=h,font_size=font,background_opacity=opacity,
                                background_only_with_messages=True, compact_background=True,
                                fade_enabled=True, auto_height=True, message_ttl_seconds=10)
        self._hud.ttl = 10
        self._hud.resize_buffer(4)
        self.translationChanged.emit()

    def _hud_screen_rect(self):
        if os.name == "nt":
            # Existing layered HUD uses Win32 desktop coordinates, not Qt DIPs.
            import ctypes
            metrics = ctypes.windll.user32.GetSystemMetrics
            return tuple(metrics(code) for code in (76,77,78,79))
        from PySide6.QtGui import QGuiApplication
        rect = QGuiApplication.primaryScreen().geometry()
        return rect.x(),rect.y(),rect.width(),rect.height()

    @Property('QVariantMap', notify=translationChanged)
    def hudPosition(self):
        x,y,w,h = self._hud_screen_rect()
        cfg = self._hud.config
        span_x,span_y = max(1,w-int(cfg.get("width",500))),max(1,h-int(cfg.get("height",150)))
        return {"x":max(0.,min(1.,(int(cfg.get("x",8))-x)/span_x)),
                "y":max(0.,min(1.,(int(cfg.get("y",360))-y)/span_y)),
                "width":min(1.,int(cfg.get("width",500))/max(1,w)),
                "height":min(1.,int(cfg.get("height",150))/max(1,h))}

    @Slot(float,float)
    def setHudPositionNormalized(self, nx, ny):
        x,y,w,h = self._hud_screen_rect()
        cfg = self._hud.config
        cfg.update(x=x+round(max(0.,min(1.,nx))*max(0,w-int(cfg.get("width",500)))),
                   y=y+round(max(0.,min(1.,ny))*max(0,h-int(cfg.get("height",150)))))
        self._hud._render()
        self.translationChanged.emit()

    @Slot()
    def resetHudPosition(self):
        from PySide6.QtGui import QGuiApplication
        from app import default_overlay_position
        screen = QGuiApplication.primaryScreen().geometry()
        x,y = default_overlay_position(screen.width(),screen.height(),
                                       self.preferences["width"],self.preferences["height"])
        self._hud.config.update(x=x+screen.x(),y=y+screen.y())
        self._hud._render()
        self.translationChanged.emit()

    @Slot()
    def testHud(self):
        if not self._hud.available: return
        if not self._overlay: self.toggle("overlay")
        if self._hud.enabled:
            self._hud.add("TEST · CoD2", "Cover me", self.trText("Тест оверлея"))

    @Slot()
    def clearHud(self):
        self._hud.clear()

    def attach_window(self, window):
        self._notice_window=window
        if os.name == "nt":
            from .tray import WindowTray
            if self._notifier:
                self._notifier.close()
            self._notifier = WindowTray(window, self.trText)
            if self._overlay_on_start and self._f8:
                self._overlay = self._hud.enable(True)
                self.changed.emit()
                self.translationChanged.emit()

    @Property(bool, constant=True)
    def experienceAvailable(self): return self._experience is not None

    @Property(bool, notify=translationChanged)
    def experienceCollect(self): return bool(self._experience and self._experience.collect)

    @Property(bool, notify=translationChanged)
    def experienceCache(self): return bool(self._experience and self._experience.cache)

    @Slot(str, bool)
    def setExperienceOption(self, key, enabled):
        if not self._experience: return
        if key == "collect":
            self._experience.set_options(enabled, self.experienceCache)
        elif key == "cache":
            self._experience.set_options(self.experienceCollect, enabled)
        self.translationChanged.emit()

    @Property('QVariantList', notify=translationChanged)
    def experienceStats(self): return list(self._experience_stats)

    @Property(int, notify=translationChanged)
    def observationCount(self):
        return self._observation_count

    @Slot()
    def refreshStats(self):
        if self._experience:
            self._experience.stats(lambda ok, data: self.ui_queue.put(("experience_action", "stats", ok, data)))

    @Slot()
    def clearExperience(self):
        if self._experience:
            self._experience.clear(lambda ok, data: self.ui_queue.put(("experience_action", "clear", ok, data)))

    @Slot(str)
    def exportExperience(self, filename):
        if not self._experience or not filename.strip(): return
        path = Path(filename).expanduser().resolve()
        if path.suffix.lower() != ".zip" or path.exists():
            self.game_status(self.trText("Укажите новый ZIP-файл"))
            self.feedback.emit("knowledge", self.translationStatus, True)
            return
        self._experience.export(path, lambda ok, data: self.ui_queue.put(("experience_action", "export", ok, data)))

    @Property(bool, notify=translationChanged)
    def knowledgeEnabled(self): return bool(knowledge_v2.RUNTIME.enabled)

    @Property(int, notify=translationChanged)
    def knowledgeVersion(self): return knowledge_v2.RUNTIME.version

    @Property(int, notify=translationChanged)
    def knowledgeCount(self): return knowledge_v2.RUNTIME.pack.count

    @Property(bool, constant=True)
    def knowledgeWritable(self): return self._knowledge_writable

    @Slot(bool)
    def setKnowledgeEnabled(self, enabled):
        knowledge_v2.RUNTIME.enabled = enabled
        self._on_log_control("map_change", "knowledge_toggle")
        self.translationChanged.emit()

    @Slot()
    def refreshKnowledge(self):
        if self._maintenance_busy or not self._knowledge_writable: return
        self._maintenance_busy = True
        self.translationChanged.emit()
        runtime = knowledge_v2.RUNTIME
        def worker():
            try: self.ui_queue.put(("qt_maintenance", "knowledge", runtime.refresh(), ""))
            except Exception as e: self.ui_queue.put(("qt_maintenance", "knowledge", False, str(e)))
        threading.Thread(target=worker, daemon=True, name="QtKnowledgeUpdate").start()

    @Property(str, notify=translationChanged)
    def updateMessage(self): return self._update_message

    @Property(bool, notify=translationChanged)
    def updateAvailable(self): return bool(self._update_url)

    @Property(str, notify=translationChanged)
    def updateNotes(self): return self._update_candidate["notes"] if self._update_candidate else ""

    @Property(bool, notify=translationChanged)
    def updateReady(self): return self._update_package is not None

    @Property(bool, constant=True)
    def updateInstallAvailable(self):
        from .preview_updates import installed_build
        return os.name=="nt" and self._store is not None and bool(installed_build())

    @Property(str, constant=True)
    def buildNumber(self):
        from .preview_updates import installed_build
        return installed_build().get("tag","source")

    @Property(str, constant=True)
    def buildSha(self):
        from .preview_updates import installed_build
        return installed_build().get("sha","")

    @Slot()
    def openUpdate(self):
        if self._update_url:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(self._update_url))

    @Slot()
    def checkUpdates(self):
        if self._maintenance_busy: return
        self.discardUpdate()
        self._maintenance_busy=True
        self._update_url=""
        self._update_candidate=None
        self._update_message=self.trText("Проверка обновлений…")
        self.translationChanged.emit()
        def worker():
            from .preview_updates import check_preview_release
            try: self.ui_queue.put(("qt_maintenance","updates",check_preview_release(),""))
            except Exception as e: self.ui_queue.put(("qt_maintenance","updates",None,str(e)))
        threading.Thread(target=worker,daemon=True,name="QtUpdateCheck").start()

    @Slot()
    def downloadUpdate(self):
        if self._maintenance_busy or not self.updateInstallAvailable or not self._update_candidate:return
        self.discardUpdate()
        self._update_cancel.clear()
        self._maintenance_busy=True
        self._update_message=self.trText("Скачивание и проверка SHA-256…")
        self.translationChanged.emit()
        candidate=dict(self._update_candidate);directory=self._store.path.parent/"updates"
        def worker():
            from .preview_updates import download_preview
            try: self.ui_queue.put(("qt_maintenance","update_download",download_preview(candidate,directory,cancelled=self._update_cancel.is_set),""))
            except Exception as e: self.ui_queue.put(("qt_maintenance","update_download",None,str(e)))
        threading.Thread(target=worker,daemon=True,name="QtUpdateDownload").start()

    @Slot()
    def discardUpdate(self):
        self._update_cancel.set()
        if self._update_package:
            try: Path(self._update_package["path"]).unlink(missing_ok=True)
            except OSError: pass
            self._update_package=None
        self.translationChanged.emit()

    @Slot()
    def installUpdate(self):
        if self._maintenance_busy or not self.updateInstallAvailable or not self._update_package:return
        from .preview_updates import verify_installer
        from PySide6.QtGui import QGuiApplication
        import subprocess
        try:
            path=verify_installer(self._update_package,self._store.path.parent/"updates")
            if not self.saveSettings():return
            subprocess.Popen([str(path)],cwd=str(path.parent),close_fds=True)
            self._update_package=None
            QGuiApplication.quit()
        except (OSError,ValueError,RuntimeError) as error:
            self._update_message=self.trText("Ошибка")+": "+str(error)
            self.translationChanged.emit()

    @Slot(str, result=str)
    def trText(self, text):
        from .ui_text import translate
        return translate(text, self.ui_language)

    @Property('QVariantList', constant=True)
    def languages(self):
        return [dict(label=label, code=code) for label, code in TARGET_LANGUAGES.items()]

    @Property('QVariantList', constant=True)
    def outgoingLanguages(self):
        return [dict(label=label, code=code) for label, code in OUTGOING_LANGUAGES.items()]

    @Property(str, notify=translationChanged)
    def outgoingSource(self): return self._out_source

    @Property(str, notify=translationChanged)
    def outgoingTarget(self): return self._out_target

    @Slot(str, str)
    def setOutgoingRoute(self, source, target):
        if source not in OUTGOING_LANGUAGES.values() or target not in OUTGOING_LANGUAGES.values():
            return
        if (source, target) == (self._out_source, self._out_target):
            return
        self._out_source, self._out_target = source, target
        if self._game:
            self._game.cancel()
            self._game.source, self._game.target = source, target
        self._outgoing_id += 1
        self._outgoing_busy = False
        self._outgoing_result = ""
        self.translationChanged.emit()

    @Slot(str, result=str)
    def shortcutStatus(self, key):
        incoming = key == "F8"
        if not (self._f8 if incoming else self._f9):
            return "Выкл"
        if self._privilege_mismatch:
            return "Несовпадение прав"
        if self._startup_elevation_denied:
            return "Запрос прав отклонён"
        game = self._game
        if game and game.hook_error or (incoming and self._hud.last_error) or (not incoming and game and game.hud.last_error):
            return "Ошибка"
        if incoming:
            if not self.logReady: return "Журнал не выбран"
            if not self._overlay: return "HUD скрыт"
            return "Ожидание сообщений"
        if game:
            if game.sending: return "Отправка"
            if game.status_error: return "Ошибка"
            if game.pending or game.preview_inflight or game.preview_due is not None: return "Перевод…"
            if game.active: return "Окно открыто"
            if time.monotonic() < game.sent_until: return "Сообщение отправлено"
            if game.ready: return "Ожидание игровой клавиши"
        return "Ручной режим"

    @Property(str, notify=translationChanged)
    def f8Status(self): return self.shortcutStatus("F8")

    @Property(str, notify=translationChanged)
    def f9Status(self): return self.shortcutStatus("F9")

    @Property(bool, notify=translationChanged)
    def gameHotkeysReady(self): return bool(self._game and self._game.ready)

    @Property(str, notify=translationChanged)
    def gameHotkeyDetail(self):
        if not self._game:
            return ""
        if self._game.hook_error:
            return self.trText("Ошибка игровых клавиш") + " · " + self._game.hook_error
        if self._game.last_shortcut:
            return self.trText("Последняя игровая клавиша") + " · " + self._game.last_shortcut
        return ""

    @Slot()
    def openShortcutLog(self):
        if self._game and self._game.diagnostics and self._game.diagnostics.path:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._game.diagnostics.path))

    @Property("QVariantMap", notify=translationChanged)
    def outgoingHudSettings(self):
        return dict(self._outgoing_hud_config)

    @Slot(result="QVariantMap")
    def defaultOutgoingHud(self):
        return outgoing_config()

    @Slot("QVariantMap", result=bool)
    def applyOutgoingHud(self, values):
        old = self._outgoing_hud_config
        self._outgoing_hud_config = outgoing_config(dict(values))
        if self._store and not self.saveSettings():
            self._outgoing_hud_config = old
            return False
        if self._game:
            self._game.cancel()
        self.translationChanged.emit()
        return True

    @Slot(result="QVariantMap")
    def outgoingScreenSize(self):
        if self._last_outgoing_rect:
            return {"width":self._last_outgoing_rect[2], "height":self._last_outgoing_rect[3]}
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return {"width":1366, "height":768}
        rect = screen.geometry()
        ratio = screen.devicePixelRatio()
        return {"width":round(rect.width()*ratio), "height":round(rect.height()*ratio)}

    @Slot(result="QVariantMap")
    def incomingDesktop(self):
        return dict(zip(("x","y","width","height"), self._hud_screen_rect()))

    @Slot(bool, result="QVariantMap")
    def incomingHudSettings(self, defaults):
        cfg = DEFAULT_CONFIG["overlay"] if defaults else self._hud.config
        return {key:cfg.get(key, value) for key,value in dict(x=8,y=360,width=500,height=150,
                font_size=10,background_opacity=.15,auto_height=True).items()}

    @Slot("QVariantMap", result=bool)
    def applyIncomingHud(self, values):
        old = self._hud.config.copy()
        self._hud.config.update({key:values[key] for key in self.incomingHudSettings(False) if key in values})
        if self._store and not self.saveSettings():
            self._hud.config = old
            return False
        self._hud._render()
        self.translationChanged.emit()
        return True

    @Slot("QVariantMap", result=str)
    def incomingHudPreview(self, values):
        from app import OverlayItem
        from incoming_hud_image import build_image
        cfg = dict(self._hud.config, **values)
        item = OverlayItem("Medic", "Cover me", self.trText("Прикрой меня"), 0)
        image, _, _, _ = build_image([item], cfg, self._hud.show_original)
        return self._preview_url(image)

    @Slot("QVariantMap", result=str)
    def outgoingHudPreview(self, values):
        screen = self.outgoingScreenSize()
        cfg = positioned(dict(values), (0,0,screen["width"],screen["height"]))
        cfg.update(route=self._out_source.upper()+" → "+self._out_target.upper(),
                   editor_labels={"title":self.trText("F9 · Исходящий перевод"),
                                  "input":self.trText("Ввод"), "translation":self.trText("Перевод")})
        image = render_editor(self.trText("Привет, давно не виделись!"), "Hey, long time no see!",
                              self.trText("Enter — отправить · Esc — отменить"), cfg)
        return self._preview_url(image)

    @staticmethod
    def _preview_url(image):
        import base64
        from io import BytesIO
        data = BytesIO()
        image.save(data, format="PNG")
        return "data:image/png;base64," + base64.b64encode(data.getvalue()).decode("ascii")

    def position_outgoing_hud(self, config):
        from app import _monitor_rect_for_window
        from outgoing_send import _foreground_api
        user32, _ = _foreground_api()
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return
        rect = _monitor_rect_for_window(hwnd)
        if rect[2] > 0 and rect[3] > 0:
            self._last_outgoing_rect = rect
            config.update(positioned(self._outgoing_hud_config, rect))

    @Property(bool, notify=translationChanged)
    def gamePrivilegeMismatch(self):
        return self._privilege_mismatch

    @Property(bool, notify=translationChanged)
    def startupElevationDenied(self): return self._startup_elevation_denied

    def markStartupElevationDenied(self):
        self._startup_elevation_denied = True
        self.game_status("Повышение прав отменено или не удалось")

    @Property(bool, notify=translationChanged)
    def gameRunning(self):
        return self._game_running

    def _check_game_privileges(self):
        from .windows_privileges import game_privilege_status
        running, mismatch = game_privilege_status()
        if (running, mismatch) != (self._game_running, self._privilege_mismatch):
            self._game_running, self._privilege_mismatch = running, mismatch
            self.translationChanged.emit()

        # A running application never elevates itself from a polling callback.
        # The mismatch is visible in the UI; only explicit confirmation restarts it.

    @Property(bool, notify=translationChanged)
    def alwaysAdmin(self): return self._always_admin

    @Slot(bool)
    def setAlwaysAdmin(self, value):
        previous = self._always_admin
        self._always_admin = value
        if self._store and not self.saveSettings():
            self._always_admin = previous
        self.translationChanged.emit()

    @Property(bool, notify=translationChanged)
    def showShortcutHint(self): return self._store is not None and not self._hint_dismissed

    @Slot()
    def dismissShortcutHint(self):
        self._hint_dismissed = True
        self.saveSettings()
        self.translationChanged.emit()

    @Slot()
    def restartElevated(self):
        if not (self._privilege_mismatch or self._startup_elevation_denied or self._always_admin) or self._store is None:
            return
        # A one-off retry does not override an explicit startup preference.
        if not self.saveSettings():
            return
        from .windows_privileges import restart_elevated
        ok, error = restart_elevated()
        if ok:
            from PySide6.QtCore import QCoreApplication
            QCoreApplication.quit()
        else:
            self.markStartupElevationDenied()
            self.feedback.emit("", self.translationStatus, True)

    @Property(bool, constant=True)
    def gameHotkeysEnabled(self): return self._game is not None

    @Property(bool, constant=True)
    def overlayAvailable(self): return self._hud.available

    @Property(bool, constant=True)
    def translationAvailable(self): return True

    @Property(bool, notify=translationChanged)
    def logReady(self): return bool(self._log_path and self._log_path.is_file())

    @Property(bool, notify=translationChanged)
    def engineReady(self): return self._started and not self.stop_event.is_set() and any(w.is_alive() for w in self._workers)

    @Property(str, constant=True)
    def appVersion(self): return APP_VERSION + " · Qt RC"

    @Property(str, notify=translationChanged)
    def translationStatus(self): return self._translation_status

    @Property(str, notify=translationChanged)
    def targetLanguage(self): return self._target

    @Property(str, notify=translationChanged)
    def logPath(self): return str(self._log_path or "")

    @Property('QVariantList', notify=translationChanged)
    def history(self): return list(self._history)

    @Property(bool, notify=translationChanged)
    def historyEnabled(self): return self._history_enabled

    @Slot(bool)
    def setHistoryEnabled(self, enabled):
        self._history_enabled = enabled
        if self._store: self.saveSettings()
        self.translationChanged.emit()

    @Slot(str)
    def copyMessage(self, text):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)

    def record_sent(self, original, translated):
        if self._history_enabled:
            self._history.appendleft(dict(nickname=self.trText("Вы"), original=original, translated=translated,
                                          direction="out", received=time.strftime("%H:%M:%S"), outcome="sent"))
            self.translationChanged.emit()

    @Slot(str, result=bool)
    def exportHistory(self, filename):
        # No automatic recording or upload. Explicit new-file export only.
        try:
            path = Path(filename).expanduser()
            if path.suffix.casefold() not in (".txt", ".json"): path = path.with_suffix(".txt")
            with path.open("x",encoding="utf-8") as stream:
                if path.suffix.lower() == ".txt":
                    for row in reversed(self._history):
                        arrow = "↑" if row.get("direction") == "out" else "↓"
                        stream.write(f"{row['received']} {arrow} {row['nickname']}\n{row['original']}\n{row['translated']}\n\n")
                else:
                    json.dump({"version":1,"received_time_basis":"local","messages":list(self._history)},stream,ensure_ascii=False,indent=2)
            self.game_status(self.trText("Экспорт сохранён") + ": " + str(path))
            self.feedback.emit("history", self.translationStatus, False)
            return True
        except OSError as error:
            self.game_status(self.trText("Ошибка") + ": " + str(error))
            self.feedback.emit("history", self.translationStatus, True)
            return False

    @Slot()
    def clearHistory(self):
        self._history.clear()
        self.translationChanged.emit()

    @Property(str, notify=translationChanged)
    def outgoingResult(self): return self._outgoing_result

    @Property(bool, notify=translationChanged)
    def outgoingBusy(self): return self._outgoing_busy

    def start(self):
        if self._started or self.stop_event.is_set():
            return
        self._started = True
        super().start()
        for worker in self._workers:
            worker.start()
        self._tailer.start()
        self._timer.start()
        self._profile_timer.start()
        if self._game:
            self._game.start()
            self._check_game_privileges()
            self._privilege_timer.start()

    def stop(self):
        if self.stop_event.is_set():
            return
        self._update_cancel.set()
        self.enabled = False
        self._timer.stop()
        self._profile_timer.stop()
        self._privilege_timer.stop()
        self.stop_event.set()
        self._dispatcher.close()
        if self._game: self._game.close()
        self._shortcut_notice.close()
        self._hud.close()
        if self._notifier: self._notifier.close()
        if self._experience:
            self._experience.close()
            if translation_memory.RUNTIME is self._experience:
                translation_memory.configure(self._previous_experience)
        super().stop()
        # No unbounded join on the GUI thread. Workers are daemon threads and
        # the program exits; do not mutate their global knowledge until stopped.
        if not self._started:
            knowledge_v2.configure(self._knowledge_previous)

    @Slot(str)
    def setLogPath(self, value):
        path = Path(value).expanduser().resolve() if value.strip() else None
        self._log_path = path
        if path: self._profiles = merge_server_profiles(self._profiles, [path])
        self._resolve_game_exe()
        self._on_log_control("map_change", "log_switch")
        self.translationChanged.emit()

    @Slot(str)
    def setTargetLanguage(self, code):
        if code in TARGET_LANGUAGES.values() and code != self._target:
            self._target = code
            self._update_settings()
            self._on_log_control("map_change", "language_change")
            self.translationChanged.emit()

    @Slot(str)
    def toggle(self, key):
        if key == "f8":
            self._f8 = self.enabled = not self._f8
            self._overlay_on_start = self._f8
            self._overlay = self._hud.enable(self._f8)
            self._on_log_control("map_change", "f8_toggle")
            self._translation_status = self.trText("Входящий перевод включён" if self._f8 else "Входящий перевод выключен")
        elif key == "f9":
            self._f9 = not self._f9
            if self._game and not self._f9: self._game.cancel()
            self._outgoing_id += 1
            self._outgoing_busy = False
            self._outgoing_result = ""
        elif key == "smart":
            self._smart = not self._smart
            if self._game: self._game.cancel()
            self._update_settings()
            self._on_log_control("map_change", "smart_toggle")
            self._outgoing_id += 1
            self._outgoing_busy = False
            self._outgoing_result = ""
        elif key == "overlay":
            # Both entry points control the same incoming feature.
            if self._f8 == self._overlay:
                self.toggle("f8")
                return
            # An unavailable HUD may leave the engine enabled. Retry enabling
            # rather than advertising a successful HUD toggle.
            if self._f8:
                self._overlay_on_start = True
                self._overlay = self._hud.enable(True)
                if self._hud.last_error:
                    self._translation_status = "HUD: " + self._hud.last_error
            else:
                self.toggle("f8")
                return
        else:
            return
        self.changed.emit()
        self.translationChanged.emit()

    @Slot(str, str, str)
    def submitOutgoing(self, text, source, target):
        if not self._f9 or self.stop_event.is_set():
            return
        if not text.strip() or len(text) > 500 or target not in OUTGOING_LANGUAGES.values():
            self._outgoing_result = self.trText("Некорректный текст или язык")
            self.translationChanged.emit()
            return
        if source != "auto" and source not in OUTGOING_LANGUAGES.values():
            return
        self._outgoing_id += 1
        self._outgoing_result = ""
        self._outgoing_busy = True
        self.translationChanged.emit()
        self._dispatcher.submit(self._outgoing_id, text, source, target, self._f8_settings)

    def _translate_outgoing(self, request_id, text, source, target, settings):
        try:
            result = translate_outgoing_text(
                text, target, source, style=settings[3], slang_enabled=settings[2],
                smart_enabled=settings[4], legacy_transform=gaming_slang_transform,
                transport=self._transport)
            self.ui_queue.put(("outgoing", request_id, True, result))
        except Exception as error:
            self.ui_queue.put(("outgoing", request_id, False, str(error)))

    @Slot()
    def _drain(self):
        if self.stop_event.is_set():
            return
        changed = False
        self._shortcut_notice.tick()
        self._hud.tick()
        if self._game: self._game.tick()
        for _ in range(100):
            try:
                event = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            kind = event[0]
            if kind == "experience_action":
                _, task, ok, data = event
                if not ok:
                    self._translation_status = self.trText("Ошибка") + ": " + str(data)
                elif task == "stats":
                    _, total, metrics = data
                    self._observation_count = total
                    self._experience_stats = [dict(group=group, **values) for group, values in sorted(metrics.items())]
                elif task == "clear":
                    self._observation_count = 0
                    self._experience_stats = []
                    self._translation_status = self.trText("Локальный опыт очищен")
                elif task == "export":
                    self._translation_status = self.trText("Экспорт сохранён") + ": " + str(data)
                if task != "stats" or not ok:
                    self.feedback.emit("stats" if task == "stats" else "knowledge", self.translationStatus, not ok)
                changed = True
                continue
            if kind == "qt_maintenance":
                _, task, result, error = event
                self._maintenance_busy = False
                if error:
                    self._translation_status = self.trText("Ошибка") + ": " + error
                    if task in ("updates","update_download"): self._update_message = self._translation_status
                elif task == "profiles":
                    self._profiles = merge_server_profiles(self._profiles, result)
                    self._resolve_game_exe()
                    if not self._log_path and self._profiles:
                        self.setLogPath(self._profiles[0]["path"])
                    elif self._auto_profile:
                        self._poll_profiles()
                    else:
                        self._profile_activity = activity_snapshot([Path(r["path"]) for r in self._profiles])
                    self._translation_status = self.trText("Профили обновлены")
                elif task == "logging":
                    self._translation_status = self.trText("Журнал игры") + f": {result.enabled_count}/{result.configs_found}; " + self.trText("После выхода из игры") + f": {result.deferred_count}; " + self.trText("Ошибка") + f": {result.failed_count}"
                elif task == "knowledge":
                    self._translation_status = self.trText("База знаний обновлена" if result else "База знаний актуальна")
                elif task == "updates":
                    self._update_candidate = result
                    self._update_url = result["url"] if result else ""
                    self._update_message = (self.trText("Доступно обновление Qt") + ": " + result["tag"]) if result else self.trText("Новых версий Qt нет")
                elif task == "update_download":
                    self._update_package=result
                    if self._update_cancel.is_set():
                        self.discardUpdate()
                        self._update_message=self.trText("Загрузка отменена")
                    else: self._update_message=self.trText("SHA-256 проверен. Можно установить обновление.")
                if task in ("profiles", "logging", "knowledge"):
                    self.feedback.emit("knowledge" if task == "knowledge" else "profiles", self.translationStatus, bool(error))
                changed = True
                continue
            if kind in ("screenshot_saved", "screenshot_error"):
                if self._game and self._game.diagnostics:
                    self._game.diagnostics.write("F10 result=%s", kind)
                self._translation_status = self._screenshot_status("saved", path=event[1]) if kind == "screenshot_saved" else self._screenshot_status("error", error=event[1])
                changed = True
                continue
            if kind == "outgoing":
                _, request_id, ok, result = event
                if request_id == self._outgoing_id:
                    self._outgoing_busy = False
                    self._outgoing_result = result if ok else self.trText("Ошибка") + ": " + result
                    changed = True
                continue
            if kind == "map_change":
                with self._shared.context_lock:
                    self._shared.context_history.clear()
                self._hud.clear()
                # Keep history for the user; stale worker results are rejected.
                continue
            if kind == "status":
                if self._translation_status != event[1]:
                    self._translation_status = event[1]
                    changed = True
                continue
            if kind not in ("translation", "same_language", "translation_error", "translation_service_busy"):
                continue
            msg = event[1]
            if not self._f8 or msg.epoch != self._chat_epoch or (msg.settings and msg.settings != self._f8_settings):
                continue
            if kind == "same_language":
                continue
            translated = event[2] if kind == "translation" else ""
            if kind == "translation":
                self._hud.add(msg.nickname, msg.text, translated)
            if self._history_enabled:
                self._history.appendleft(dict(direction="in", nickname=msg.nickname, original=msg.text, received=time.strftime("%H:%M:%S"),
                                          translated=translated, outcome=kind,
                                          elapsed=event[3] if kind == "translation" else 0))
            self._translation_status = self.t("translation_done").format(elapsed_ms=event[3]) if kind == "translation" else self.t("translation_service_busy") if kind == "translation_service_busy" else self.t("translation_unavailable").format(error=event[2])
            changed = True
        if self._overlay != self._hud.enabled:
            self._overlay = self._hud.enabled
            self._translation_status = "HUD: " + self._hud.last_error
            self.changed.emit()
            changed = True
        if changed:
            self.translationChanged.emit()
