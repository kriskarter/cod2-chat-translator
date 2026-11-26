"""Working translation services with no Tk event loop or Tk widgets.

The existing application's algorithms are reused exactly. This development
runtime is opt-in, reads the supplied configuration, and never writes it.
"""
from __future__ import annotations

import json
import os
import queue
import threading
from collections import deque
from pathlib import Path

from PySide6.QtCore import QTimer, Signal, Slot, Property
from app import (ControlApp, DEFAULT_CONFIG, UI_STRINGS, TARGET_LANGUAGES,
                 SLANG_STYLES, LogTailer, TranslatorWorker,
                 TranslationWorkerSharedState, RecentDuplicateFilter,
                 deep_merge, gaming_slang_transform)
from outgoing_chat import (OutgoingTranslationDispatcher, OutgoingHttpTransport,
                           translate_outgoing_text)
import knowledge_v2
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
        self.ui_language = config.get("ui_language", "ru")
        self._translation_status = "Ожидание запуска"
        self._history = deque(maxlen=200)
        self._outgoing_result = ""
        self._outgoing_busy = False
        self._outgoing_id = 0
        self._f8 = self.enabled = True
        self._f9 = True
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
        self.stop_event = threading.Event()
        self.translation_jobs = queue.Queue(maxsize=50)
        self.ui_queue = queue.Queue()
        self.duplicate_filter = RecentDuplicateFilter(float(config.get("duplicate_window_seconds", 4)))
        self._arrival_context = deque(maxlen=24)
        self._chat_epoch = 0
        self._hud = NativeHud(config.get("overlay", {}), config.get("show_original", False))
        self._knowledge_previous = knowledge_v2.RUNTIME
        bundled = ROOT / "assets" / "knowledge_v2.json"
        runtime = knowledge_v2.KnowledgeRuntime(bundled, installed_knowledge or bundled)
        runtime.enabled = bool(config.get("knowledge_v2_enabled", True))
        knowledge_v2.configure(runtime)
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
                                self.stop_event, self._on_log_control, self.t)
        self._transport = OutgoingHttpTransport()
        self._dispatcher = OutgoingTranslationDispatcher(
            self._translate_outgoing, on_worker_exit=self._transport.close_current_thread)
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._drain)
        self._started = False
        self._game = None
        self._screenshot_in_progress = False
        if game_hotkeys and os.name == "nt":
            from .game_controls import GameControls
            self._game = GameControls(self, config.get("overlay", {}),
                                      config.get("outgoing_source_language", self.ui_language),
                                      config.get("outgoing_target_language", "en"))

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
        self._translation_status = text
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
                      log_path=str(self._log_path or ""), active_profile_path=str(self._log_path or ""),
                      server_monitor=dump_settings(self._settings))
        try:
            self._store.save(config)
            self._config = config
            self.game_status("Настройки сохранены")
        except (OSError, RuntimeError) as error:
            self.game_status("Ошибка сохранения: " + str(error))

    def _settings_changed(self):
        # Save only on explicit user request, never from a network callback.
        pass

    @Property('QVariantList', constant=True)
    def languages(self):
        return [dict(label=label, code=code) for label, code in TARGET_LANGUAGES.items()]

    @Property(bool, notify=translationChanged)
    def gameHotkeysReady(self): return bool(self._game and self._game.ready)

    @Property(bool, constant=True)
    def gameHotkeysEnabled(self): return self._game is not None

    @Property(bool, constant=True)
    def overlayAvailable(self): return self._hud.available

    @Property(bool, constant=True)
    def translationAvailable(self): return True

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
        if self._game: self._game.start()

    def stop(self):
        if self.stop_event.is_set():
            return
        self.enabled = False
        self._timer.stop()
        self.stop_event.set()
        self._dispatcher.close()
        if self._game: self._game.close()
        self._hud.close()
        super().stop()
        # No unbounded join on the GUI thread. Workers are daemon threads and
        # the program exits; do not mutate their global knowledge until stopped.
        if not self._started:
            knowledge_v2.configure(self._knowledge_previous)

    @Slot(str)
    def setLogPath(self, value):
        path = Path(value).expanduser().resolve() if value.strip() else None
        self._log_path = path
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
            self._translation_status = "Входящий перевод включён" if self._f8 else "Входящий перевод выключен"
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
        if not text.strip() or len(text) > 500 or target not in TARGET_LANGUAGES.values():
            self._outgoing_result = "Некорректный текст или язык"
            self.translationChanged.emit()
            return
        if source != "auto" and source not in TARGET_LANGUAGES.values():
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
            self._history.appendleft(dict(nickname=msg.nickname, original=msg.text,
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
