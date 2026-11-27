"""Opt-in game integration. Qt owns the existing native hook and HUD."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import threading
import time
from PySide6.QtGui import QGuiApplication
from outgoing_chat import (KeyboardCapture, OutgoingTranslationDispatcher,
                           OutgoingHttpTransport, translate_outgoing_text,
                           normalize_outgoing_text)
from outgoing_send import is_cod2_foreground, send_cod2_chat_message
from app import gaming_slang_transform
from .native_hud import NativeHud
from .shortcut_diagnostics import ShortcutDiagnostics, NAMES, SHORTCUTS


class GameControls:
    def __init__(self, state, config, source, target, *, foreground=is_cod2_foreground,
                 keyboard_factory=KeyboardCapture, hud_factory=NativeHud,
                 translator=translate_outgoing_text, sender=send_cod2_chat_message):
        self.state = state
        self.source, self.target = source, target
        self.foreground = foreground
        self.translator, self.sender = translator, sender
        self.events = queue.Queue()
        self.keyboard = keyboard_factory(self.events, game_scope=self._focused)
        self.keyboard.set_enabled(state.f9)
        self.hud = hud_factory({**config, "max_messages": 1, "message_ttl_seconds": 120,
                                "background_opacity": .75, "height": max(140, int(config.get("height", 150))),
                                "y": int(config.get("y", 360)) + 165}, True)
        self.transport = OutgoingHttpTransport()
        self.dispatcher = OutgoingTranslationDispatcher(self._translate, on_worker_exit=self.transport.close_current_thread)
        self.active = False
        self.pending = False
        self.sending = False
        self.ready = False
        self.hook_error = ""
        self.last_shortcut = ""
        self.buffer = ""
        self.generation = 0
        self.preview_due = None
        self.preview_inflight = False
        self.preview_result = ""
        self.closed = threading.Event()
        self.diagnostics = None
        self.rearming = False
        self.resume_f9 = False

    def _focused(self):
        try:
            return not self.closed.is_set() and self.foreground()
        except Exception:
            return False

    def start(self):
        if os.name == "nt" and isinstance(self.keyboard, KeyboardCapture):
            store = getattr(self.state, "_store", None)
            folder = store.path.parent if store else Path(os.environ["APPDATA"]) / "CoD2ChatTranslatorQtPreview"
            try:
                self.diagnostics = ShortcutDiagnostics(folder)
                self.keyboard.shortcut_trace = self.diagnostics.edges
            except OSError:
                pass
        self.keyboard.start()

    def close(self):
        self.closed.set()
        self.cancel()
        self.keyboard.stop()
        if self.diagnostics:
            self.diagnostics.close()
            self.diagnostics = None
        self.dispatcher.close()
        self.hud.close()

    def cancel(self, message=""):
        self.generation += 1
        self.active = self.pending = False
        self.preview_due = None
        self.preview_inflight = False
        self.preview_result = ""
        self.buffer = ""
        self.keyboard.set_active(False)
        self.hud.enable(False)
        if message:
            self.state.game_status(message)

    def _display(self, caption, translation=""):
        self.hud.items.clear()
        tr = getattr(self.state, "trText", lambda value: value)
        self.hud.add("F9 · " + tr(caption), self.buffer, translation or self.buffer or tr("Введите сообщение…"))
        if not self.hud.enabled:
            self.cancel("F9 HUD недоступен: " + self.hud.last_error)

    def open(self):
        if not self.state.f9 or not self._focused() or self.sending:
            return
        self.state.position_outgoing_hud(self.hud.config)
        if not self.hud.enable(True):
            self.state.game_status("F9 HUD недоступен: " + self.hud.last_error)
            return
        self.active = True
        self.buffer = ""
        self.keyboard.set_active(True)
        self._display("Enter — отправить · Esc — отменить")

    def _edit(self):
        # Every edit invalidates a previous translation before another job is queued.
        self.generation += 1
        self.preview_inflight = False
        self.preview_result = ""
        self.preview_due = time.monotonic() + .32 if self.buffer.strip() else None
        self._display("Enter — отправить · Esc — отменить")

    def _request_preview(self):
        text = normalize_outgoing_text(self.buffer)
        self.preview_due = None
        if not text or not self.active:
            return
        self.preview_inflight = True
        self.dispatcher.submit(self.generation, text, self.state._f8_settings, self.source, self.target)

    def submit(self):
        if not self.active or self.pending or not self._focused():
            return
        if not normalize_outgoing_text(self.buffer):
            return
        if self.preview_result:
            self._begin_send(self.preview_result)
            return
        self.pending = True
        self._display("Перевод… Esc — отменить")
        if self.active and not self.preview_inflight:
            self._request_preview()

    def _translate(self, generation, text, settings, source, target):
        try:
            result = self.translator(text, target, source, style=settings[3],
                                     slang_enabled=settings[2], smart_enabled=settings[4],
                                     legacy_transform=gaming_slang_transform, transport=self.transport)
            if not result or not result.strip():
                raise ValueError("Пустой перевод")
            self.events.put(("result", (generation, True, result)))
        except Exception as error:
            self.events.put(("result", (generation, False, str(error))))

    def _begin_send(self, result):
        if not self.active or not self._focused() or not self.state.f9:
            self.cancel("F9: фокус CoD2 потерян")
            return
        self.cancel()
        self.sending = True
        self.state.game_status("F9: отправка в CoD2")
        threading.Thread(target=self._send, args=(result,), daemon=True,
                         name="QtCoD2GameSend").start()

    def _send(self, text):
        try:
            if not self._focused() or not self.state.f9:
                ok, error = False, "Фокус CoD2 потерян"
            else:
                ok, error = self.sender(text)
            self.events.put(("sent", (ok, error)))
        except Exception as error:
            self.events.put(("sent", (False, str(error))))

    def tick(self):
        if self.closed.is_set():
            return
        self.keyboard.set_enabled(self.state.f9)
        if self.active and (not self._focused() or not self.state.f9 or not self.keyboard.active):
            self.cancel("F9: ввод отменён")
        diag = self.diagnostics
        if self.rearming and not self.keyboard._thread.is_alive():
            self.keyboard = KeyboardCapture(self.events, game_scope=self._focused)
            self.keyboard.set_enabled(self.state.f9)
            self.keyboard.shortcut_trace = diag.edges
            self.keyboard.start()
            self.rearming = False
        if diag:
            now = time.monotonic()
            for missed in diag.missed(self.keyboard, now):
                focused = self._focused()
                diag.write("async_edge key=%s game_focus=%s %s", NAMES[missed], focused, diag.focus())
                if not focused:
                    continue
                if missed == "toggle_popup" and self.state.f9 and not self.rearming:
                    if self.active:
                        self.cancel()
                    else:
                        self.resume_f9 = True
                    # Reinstall before opening text input after a missed hook edge.
                    self.keyboard.stop()
                    self.ready = False
                    self.rearming = True
                    diag.write("F9 hook_rearm")
                elif missed != "toggle_popup":
                    self.events.put((missed, "poll"))
            if now - diag.heartbeat >= 30:
                diag.heartbeat = now
                diag.write("qt_tick hook_thread_alive=%s queue=%d", self.keyboard._thread.is_alive(), self.events.qsize())
        for _ in range(100):
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break
            if diag:
                if event == "shortcut_hook":
                    vk, injected, accepted, enabled = value
                    diag.write("hook_edge key=%s injected=%s game_focus_at_hook=%s f9_enabled=%s qt_dequeued=yes current_%s",
                               NAMES[SHORTCUTS[vk]], injected, accepted, enabled, diag.focus())
                elif event in NAMES:
                    diag.write("qt_dispatch key=%s source=%s focus=%s", NAMES[event], value or "hook", self._focused())
                elif event in ("hook_ready", "hook_error"):
                    diag.write("%s %s", event, value or "")
            if event == "hook_ready":
                self.ready = True
                self.hook_error = ""
                self.state.game_status("Игровые клавиши готовы")
                if self.resume_f9 and not self.rearming:
                    self.resume_f9 = False
                    if self._focused() and self.state.f9:
                        self.events.put(("toggle_popup", "rearmed"))
            elif event == "hook_error":
                self.ready = False
                self.resume_f9 = False
                self.hook_error = str(value)
                self.cancel(self.hook_error)
            elif event == "f8" and self._focused():
                self.last_shortcut = "F8"
                self.state.toggle("overlay")
                if diag: diag.write("F8 overlay_enabled=%s", self.state.overlay)
            elif event == "screenshot" and self._focused():
                self.last_shortcut = "F10"
                self.state.capture_game_screenshot()
                if diag: diag.write("F10 capture_requested")
            elif event == "toggle_popup" and self._focused():
                self.last_shortcut = "F9"
                self.state.game_status("F9")
                if self.active:
                    self.cancel("F9: ввод закрыт")
                else:
                    self.open()
                if diag: diag.write("F9 input_active=%s hud_enabled=%s hud_error=%s", self.active, self.hud.enabled, self.hud.last_error)
            elif event in ("cancel", "system_escape"):
                self.cancel("F9: ввод отменён")
            elif event == "submit":
                self.submit()
            elif event == "result":
                generation, ok, result = value
                if not self.active or generation != self.generation:
                    continue
                self.preview_inflight = False
                if not self._focused() or not self.state.f9:
                    self.cancel("F9: фокус CoD2 потерян")
                elif not ok:
                    self.pending = False
                    self.preview_result = ""
                    self._display("Ошибка перевода · повторите Enter")
                    self.state.game_status(result)
                elif self.pending:
                    self._begin_send(result)
                else:
                    self.preview_result = result
                    self._display("Enter — отправить · Esc — отменить", result)
            elif event == "sent":
                self.sending = False
                ok, error = value
                self.state.game_status("F9: отправлено" if ok else "F9: " + error)
            elif self.active and not self.pending:
                if event == "text":
                    self.buffer = (self.buffer + str(value))[:500]
                elif event == "backspace":
                    self.buffer = self.buffer[:-1]
                elif event == "paste":
                    self.buffer = (self.buffer + QGuiApplication.clipboard().text())[:500]
                else:
                    continue
                self._edit()
        if self.active and not self.pending and self.preview_due is not None and time.monotonic() >= self.preview_due:
            self._request_preview()
