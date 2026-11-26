"""Working translation services with no Tk event loop or Tk widgets.

The existing application's algorithms are reused exactly. This development
runtime is opt-in, reads the supplied configuration, and never writes it.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QTimer, Signal, Slot, Property
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
from .common import ROOT
from .native_hud import NativeHud
from server_monitor import load_settings, dump_settings


def read_translation_config(path: Path | None):
    if path is None:
        return deep_merge(DEFAULT_CONFIG, {})
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration root must be an object")
    return deep_merge(DEFAULT_CONFIG, raw)


class TranslationState(LiveMonitorState):
    translationChanged = Signal()
    # These existing methods access only the ingress contract below, not Tk.
    # Keeping one algorithm preserves deduplication, context and local fast path.
    on_log_message = ControlApp.on_log_message
    _on_log_control = ControlApp._on_log_control

    def __init__(self, config, game_exe=None, log_path=None, installed_knowledge=None, game_hotkeys=False, settings_store=None):
        super().__init__(load_settings(config.get("server_monitor")), game_exe)
        self._config = config
        self._store = settings_store
        self._profiles = merge_server_profiles(config.get("server_profiles"), [])
        self._auto_profile = bool(config.get("auto_detect_profile", True))
        self._profile_activity = {}
        self._pending_switch_positions = {}
        self._last_profile_scan = time.monotonic()
        self._notifications = deque(maxlen=80)
        self._friend_presence = {}
        self._friend_notice_at = {}
        self._maintenance_busy = False
        self._update_message = ""
        self._update_url = ""
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
        self._hud = NativeHud(config.get("overlay", {}), config.get("show_original", False))
        self._notifier = None
        self._experience = None
        self._previous_experience = translation_memory.RUNTIME
        self._experience_stats = []
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
            self._game = GameControls(self, config.get("overlay", {}),
                                      self._out_source, self._out_target)

    _screenshot_directory = ControlApp._screenshot_directory
    _screenshot_status = ControlApp._screenshot_status
    def _capture_game_screenshot_worker(self):
        # Never fall back to capturing a different application or whole desktop.
        import time
        from PIL import ImageGrab
        from app import find_cod2_window, _monitor_rect_for_window
        from outgoing_send import is_cod2_foreground
        try:
            if not is_cod2_foreground():
                raise RuntimeError("CoD2 не в фокусе")
            hwnd = find_cod2_window()
            if not hwnd:
                raise RuntimeError("Окно CoD2 не найдено")
            left, top, width, height = _monitor_rect_for_window(hwnd)
            if width <= 0 or height <= 0 or not is_cod2_foreground():
                raise RuntimeError("Окно CoD2 недоступно")
            image = ImageGrab.grab(bbox=(left, top, left+width, top+height),
                                   include_layered_windows=True, all_screens=True)
            path = self._screenshot_directory() / f"CoD2_Chat_Translator_{time.strftime('%Y-%m-%d_%H-%M-%S')}_{time.time_ns()%1000000000:09d}.png"
            image.save(path, format="PNG")
            self.ui_queue.put(("screenshot_saved", str(path)))
        except Exception as error:
            self.ui_queue.put(("screenshot_error", str(error)))
        finally:
            self._screenshot_in_progress = False

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
        config.update(target_language=self._target, smart_engine_enabled=self._smart,
                      qt_f8_enabled=self._f8, outgoing_enabled=self._f9,
                      outgoing_source_language=self._out_source, outgoing_target_language=self._out_target,
                      log_path=str(self._log_path or ""), active_profile_path=str(self._log_path or ""),
                      server_monitor=dump_settings(self._settings), ui_language=self.ui_language,
                      server_profiles=self._profiles, auto_detect_profile=self._auto_profile,
                      knowledge_v2_enabled=knowledge_v2.RUNTIME.enabled,
                      hide_same_language=self._hide, gaming_slang=self._slang,
                      deduplicate_messages=self._dedupe, slang_style=self._style,
                      show_original=self._hud.show_original, overlay=dict(self._hud.config),
                      experience_collect=bool(self._experience and self._experience.collect),
                      experience_cache=bool(self._experience and self._experience.cache))
        try:
            self._store.save(config)
            self._config = config
            self.game_status("Настройки сохранены")
        except (OSError, RuntimeError) as error:
            self.game_status(self.trText("Ошибка сохранения") + ": " + str(error))

    def _settings_changed(self):
        # Save only on explicit user request, never from a network callback.
        pass

    @Property(str, notify=translationChanged)
    def uiLanguage(self): return self.ui_language

    @Slot(str)
    def setUiLanguage(self, code):
        if code in ("ru", "uk", "en") and code != self.ui_language:
            self.ui_language = code
            self.translationChanged.emit()
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
        self._settings["notify_friends"] = enabled
        self.translationChanged.emit()

    @Slot(object)
    def _apply_snapshot(self, snapshot):
        super()._apply_snapshot(snapshot)
        from server_monitor import normalized_name
        import time
        if snapshot.address not in self._rows: return
        if snapshot.state != "online":
            self._friend_presence.pop(snapshot.address, None)
            return
        friends = {normalized_name(n): n for n in self._settings["friends"]}
        current = {normalized_name(p.name) for p in snapshot.players}
        previous = self._friend_presence.get(snapshot.address)
        self._friend_presence[snapshot.address] = current
        if previous is None or not self.notifyFriends: return
        for name in sorted((current - previous) & friends.keys()):
            key = (snapshot.address, name)
            now = time.monotonic()
            if now - self._friend_notice_at.get(key, -1e9) < 600: continue
            self._friend_notice_at[key] = now
            title = self.trText("Друг в игре")
            detail = friends[name] + " · " + (snapshot.name or snapshot.address)
            self._notifications.appendleft(title + ": " + detail)
            if self._notifier: self._notifier.show(title, detail)
            self.translationChanged.emit()

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

    @Slot(str)
    def applyHudPreset(self, preset):
        values = {"text":(420,120,9,0.),"minimal":(420,120,9,.15),"readable":(500,150,10,.12)}.get(preset)
        if values is None: return
        w,h,font,opacity = values
        self._hud.config.update(width=w,height=h,font_size=font,background_opacity=opacity,
                                background_only_with_messages=True, compact_background=True,
                                fade_enabled=True, auto_height=True, message_ttl_seconds=10)
        self._hud.ttl = 10
        self._hud.resize_buffer(4)
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
        if os.name == "nt":
            from windows_friend_notice import FriendNotice
            self._notifier = FriendNotice(int(window.winId()))

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

    @Slot()
    def openUpdate(self):
        if self._update_url:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(self._update_url))

    @Slot()
    def checkUpdates(self):
        if self._maintenance_busy: return
        self._maintenance_busy = True
        self._update_url = ""
        self.translationChanged.emit()
        def worker():
            from .preview_updates import check_preview_release
            try:
                self.ui_queue.put(("qt_maintenance", "updates", check_preview_release(), ""))
            except Exception as e:
                self.ui_queue.put(("qt_maintenance", "updates", None, str(e)))
        threading.Thread(target=worker, daemon=True, name="QtUpdateCheck").start()

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

    @Property(bool, notify=translationChanged)
    def gameHotkeysReady(self): return bool(self._game and self._game.ready)

    @Property(bool, constant=True)
    def gameHotkeysEnabled(self): return self._game is not None

    @Property(bool, constant=True)
    def overlayAvailable(self): return self._hud.available

    @Property(bool, constant=True)
    def translationAvailable(self): return True

    @Property(bool, notify=translationChanged)
    def logReady(self): return bool(self._log_path and self._log_path.is_file())

    @Property(bool, notify=translationChanged)
    def engineReady(self): return self._started and not self.stop_event.is_set()

    @Property(str, constant=True)
    def appVersion(self): return APP_VERSION + " · Qt Preview"

    @Property(str, notify=translationChanged)
    def translationStatus(self): return self._translation_status

    @Property(str, notify=translationChanged)
    def targetLanguage(self): return self._target

    @Property(str, notify=translationChanged)
    def logPath(self): return str(self._log_path or "")

    @Property('QVariantList', notify=translationChanged)
    def history(self): return list(self._history)

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
        if self._game: self._game.start()

    def stop(self):
        if self.stop_event.is_set():
            return
        self.enabled = False
        self._timer.stop()
        self._profile_timer.stop()
        self.stop_event.set()
        self._dispatcher.close()
        if self._game: self._game.close()
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
            self._overlay = self._hud.enable(not self._overlay)
            if self._hud.last_error:
                self._translation_status = "HUD: " + self._hud.last_error
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
        changed = False
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
                    count, total, metrics = data
                    self._experience_stats = [dict(group="Total", samples=total, failed=0, p50_ms="—", p95_ms="—")]
                    self._experience_stats.extend(dict(group=group, **values) for group, values in sorted(metrics.items()))
                elif task == "clear":
                    self._experience_stats = []
                    self._translation_status = self.trText("Локальный опыт очищен")
                elif task == "export":
                    self._translation_status = self.trText("Экспорт сохранён") + ": " + str(data)
                changed = True
                continue
            if kind == "qt_maintenance":
                _, task, result, error = event
                self._maintenance_busy = False
                if error:
                    self._translation_status = self.trText("Ошибка") + ": " + error
                    if task == "updates": self._update_message = self._translation_status
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
                    self._update_url = result["url"] if result else ""
                    self._update_message = (self.trText("Доступно обновление Qt") + ": " + result["tag"]) if result else self.trText("Новых версий Qt нет")
                changed = True
                continue
            if kind in ("screenshot_saved", "screenshot_error"):
                self._translation_status = self._screenshot_status("saved", path=event[1]) if kind == "screenshot_saved" else self._screenshot_status("error", error=event[1])
                changed = True
                continue
            if kind == "outgoing":
                _, request_id, ok, result = event
                if request_id == self._outgoing_id:
                    self._outgoing_busy = False
                    self._outgoing_result = result if ok else "Ошибка: " + result
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
            self._history.appendleft(dict(nickname=msg.nickname, original=msg.text, received=time.strftime("%H:%M:%S"),
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
