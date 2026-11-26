"""Opt-in game integration. Qt owns the existing native hook and HUD."""
from __future__ import annotations

import queue
import threading
from PySide6.QtGui import QGuiApplication
from outgoing_chat import (KeyboardCapture, OutgoingTranslationDispatcher,
                           OutgoingHttpTransport, translate_outgoing_text,
                           normalize_outgoing_text)
from outgoing_send import is_cod2_foreground, send_cod2_chat_message
from app import gaming_slang_transform
from .native_hud import NativeHud


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
        self.buffer = ""
        self.generation = 0
        self.closed = threading.Event()

    def _focused(self):
        try:
            return not self.closed.is_set() and self.foreground()
        except Exception:
            return False

    def start(self):
        self.keyboard.start()

    def close(self):
        self.closed.set()
        self.cancel()
        self.keyboard.stop()
        self.dispatcher.close()
        self.hud.close()

    def cancel(self, message=""):
        self.generation += 1
        self.active = self.pending = False
        self.buffer = ""
        self.keyboard.set_active(False)
        self.hud.enable(False)
        if message:
            self.state.game_status(message)

    def _display(self, caption):
        self.hud.items.clear()
        self.hud.add("F9 · " + caption, self.buffer, self.buffer or "Введите сообщение…")
        if not self.hud.enabled:
            self.cancel("F9 HUD недоступен: " + self.hud.last_error)

    def open(self):
        if not self.state.f9 or not self._focused() or self.sending:
            return
        if not self.hud.enable(True):
            self.state.game_status("F9 HUD недоступен: " + self.hud.last_error)
            return
        self.active = True
        self.buffer = ""
        self.keyboard.set_active(True)
        self._display("Enter — отправить · Esc — отменить")

    def submit(self):
        if not self.active or self.pending or not self._focused():
            return
        text = normalize_outgoing_text(self.buffer)
        if not text:
            return
        self.pending = True
        self.generation += 1
        self._display("Перевод… Esc — отменить")
        if self.active:
            self.dispatcher.submit(self.generation, text, self.state._f8_settings)

    def _translate(self, generation, text, settings):
        try:
            result = self.translator(text, self.target, self.source, style=settings[3],
                                     slang_enabled=settings[2], smart_enabled=settings[4],
                                     legacy_transform=gaming_slang_transform, transport=self.transport)
            self.events.put(("result", (generation, True, result)))
        except Exception as error:
            self.events.put(("result", (generation, False, str(error))))

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
        for _ in range(100):
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "hook_ready":
                self.ready = True
                self.state.game_status("Игровые клавиши готовы")
            elif event == "hook_error":
                self.ready = False
                self.cancel(str(value))
            elif event == "f8" and self._focused():
                self.state.toggle("overlay")
            elif event == "screenshot" and self._focused():
                self.state.capture_game_screenshot()
            elif event == "toggle_popup":
                if self.active:
                    self.cancel("F9: ввод закрыт")
                else:
                    self.open()
            elif event in ("cancel", "system_escape"):
                self.cancel("F9: ввод отменён")
            elif event == "submit":
                self.submit()
            elif event == "result":
                generation, ok, result = value
                if not self.active or not self.pending or generation != self.generation:
                    continue
                if not self._focused() or not self.state.f9:
                    self.cancel("F9: фокус CoD2 потерян")
                elif not ok:
                    self.pending = False
                    self._display("Ошибка перевода · повторите Enter")
                    self.state.game_status(result)
                else:
                    self.cancel()
                    self.sending = True
                    self.state.game_status("F9: отправка в CoD2")
                    threading.Thread(target=self._send, args=(result,), daemon=True,
                                     name="QtCoD2GameSend").start()
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
                self._display("Enter — отправить · Esc — отменить")
