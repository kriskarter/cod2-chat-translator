from __future__ import annotations

import ctypes
import os
import queue
import re
import threading
import time
from ctypes import wintypes

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    tk = None
    ttk = None


APP_TITLE = "CoD2 Outgoing Chat Prototype"
TARGET_CODE = "en"
TARGET_NAME = "English"

VK_F9 = 0x78
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
HOTKEY_ID = 0xC0D2


def normalize_outgoing_text(text: str) -> str:
    text = (text or "").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def translate_outgoing_text(text: str, target: str = TARGET_CODE) -> str:
    from deep_translator import GoogleTranslator

    source = normalize_outgoing_text(text)
    if not source:
        raise ValueError("Пустое сообщение")

    translated = GoogleTranslator(
        source="auto",
        target=target,
    ).translate(source)

    translated = normalize_outgoing_text(str(translated or ""))
    if not translated:
        raise RuntimeError("Сервис перевода вернул пустой ответ")

    return translated


class GlobalF9Hotkey:
    """Poll F9 the same way the main translator polls its proven F8 hotkey."""

    def __init__(self, events: queue.Queue) -> None:
        self.events = events

    def start(self) -> None:
        threading.Thread(
            target=self._run,
            daemon=True,
            name="OutgoingChatF9",
        ).start()

    def _run(self) -> None:
        if os.name != "nt":
            self.events.put(("hotkey_error", "F9 доступен только в Windows"))
            return

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            user32.GetAsyncKeyState.restype = ctypes.c_short
        except Exception as exc:
            self.events.put(("hotkey_error", f"Не удалось инициализировать F9: {exc}"))
            return

        self.events.put(("hotkey_ready", None))

        previous_down = False

        while True:
            try:
                down = bool(user32.GetAsyncKeyState(VK_F9) & 0x8000)

                if down and not previous_down:
                    self.events.put(("toggle_popup", None))

                previous_down = down
                time.sleep(0.025)

            except Exception as exc:
                self.events.put(("hotkey_error", f"Ошибка F9: {exc}"))
                return


class OutgoingChatPrototype:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("520x270")
        self.root.minsize(500, 250)

        self.events: queue.Queue = queue.Queue()

        self.previous_foreground = 0
        self.popup_visible = False
        self.mode = "input"
        self.translation_in_progress = False
        self.last_translation = ""

        self.status_var = tk.StringVar(
            value="Запускаю глобальную клавишу F9…"
        )
        self.last_var = tk.StringVar(
            value="Последний перевод: —"
        )

        self._build_control_window()
        self._build_popup()

        GlobalF9Hotkey(self.events).start()

        self.root.after(40, self._poll_events)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _build_control_window(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Исходящий чат — прототип",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            outer,
            text=(
                "Локальный тест. Эта версия НЕ отправляет "
                "сообщения в Call of Duty 2."
            ),
            foreground="#a33",
        ).pack(anchor="w", pady=(6, 14))

        info = ttk.LabelFrame(
            outer,
            text="Как пользоваться",
            padding=12,
        )
        info.pack(fill="x")

        ttk.Label(
            info,
            text="F9 — открыть / скрыть поле сообщения",
        ).pack(anchor="w")

        ttk.Label(
            info,
            text=f"Перевод исходящего текста → {TARGET_NAME}",
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(
            info,
            text="Enter — перевести · Esc — закрыть",
        ).pack(anchor="w", pady=(4, 0))

        ttk.Button(
            outer,
            text="Открыть тестовое окно",
            command=self.toggle_popup,
        ).pack(anchor="w", pady=(14, 6))

        ttk.Label(
            outer,
            textvariable=self.status_var,
        ).pack(anchor="w", pady=(4, 0))

        ttk.Label(
            outer,
            textvariable=self.last_var,
            wraplength=470,
        ).pack(anchor="w", pady=(8, 0))

    def _build_popup(self) -> None:
        popup = tk.Toplevel(self.root)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#101419")

        frame = tk.Frame(
            popup,
            bg="#101419",
            highlightthickness=1,
            highlightbackground="#424a55",
        )
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg="#101419")
        header.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(
            header,
            text="СООБЩЕНИЕ ВСЕМ",
            bg="#101419",
            fg="#f0f2f5",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text=f"→ {TARGET_NAME}",
            bg="#101419",
            fg="#67d4ff",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right")

        self.entry_var = tk.StringVar()

        self.entry = tk.Entry(
            frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 13),
            bg="#1c222a",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
        )
        self.entry.pack(
            fill="x",
            padx=16,
            ipady=8,
        )

        self.preview = tk.Label(
            frame,
            text="",
            bg="#101419",
            fg="#9de5a7",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self.preview.pack(
            fill="x",
            padx=16,
            pady=(9, 0),
        )

        self.hint = tk.Label(
            frame,
            text="Enter — перевести    Esc — закрыть",
            bg="#101419",
            fg="#8f98a5",
            font=("Segoe UI", 9),
        )
        self.hint.pack(
            anchor="w",
            padx=16,
            pady=(7, 11),
        )

        self.popup = popup

        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Escape>", self._on_escape)
        popup.bind("<Escape>", self._on_escape)

    def _remember_foreground(self) -> None:
        if os.name != "nt":
            return

        try:
            hwnd = int(ctypes.windll.user32.GetForegroundWindow())
            if hwnd:
                self.previous_foreground = hwnd
        except Exception:
            self.previous_foreground = 0

    def _force_foreground_window(self, hwnd: int) -> bool:
        """Temporarily attach input queues so Windows allows a foreground switch."""
        if os.name != "nt" or not hwnd:
            return False

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            foreground = int(user32.GetForegroundWindow() or 0)
            current_tid = int(kernel32.GetCurrentThreadId())
            target_tid = int(user32.GetWindowThreadProcessId(hwnd, None) or 0)
            foreground_tid = (
                int(user32.GetWindowThreadProcessId(foreground, None) or 0)
                if foreground
                else 0
            )

            attached_foreground = False
            attached_target = False

            try:
                if foreground_tid and foreground_tid != current_tid:
                    attached_foreground = bool(
                        user32.AttachThreadInput(
                            current_tid,
                            foreground_tid,
                            True,
                        )
                    )

                if target_tid and target_tid != current_tid:
                    attached_target = bool(
                        user32.AttachThreadInput(
                            current_tid,
                            target_tid,
                            True,
                        )
                    )

                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.SetActiveWindow(hwnd)
                user32.SetFocus(hwnd)

                return int(user32.GetForegroundWindow() or 0) == int(hwnd)

            finally:
                if attached_target:
                    user32.AttachThreadInput(
                        current_tid,
                        target_tid,
                        False,
                    )

                if attached_foreground:
                    user32.AttachThreadInput(
                        current_tid,
                        foreground_tid,
                        False,
                    )

        except Exception:
            return False

    def _focus_popup_for_typing(self) -> None:
        if not self.popup_visible:
            return

        try:
            self.popup.lift()
            self.popup.attributes("-topmost", True)
            self.popup.update_idletasks()

            popup_hwnd = int(self.popup.winfo_id())

            self._force_foreground_window(popup_hwnd)

            self.entry.focus_set()
            self.entry.icursor("end")
        except Exception:
            try:
                self.entry.focus_force()
            except Exception:
                pass

    def _restore_foreground(self) -> None:
        if os.name != "nt" or not self.previous_foreground:
            return

        self._force_foreground_window(
            self.previous_foreground
        )

    def _position_popup(self) -> None:
        width = 720
        height = 150

        sw = self.popup.winfo_screenwidth()
        sh = self.popup.winfo_screenheight()

        x = max(10, (sw - width) // 2)
        y = max(10, int(sh * 0.72))

        self.popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def show_popup(self) -> None:
        if self.popup_visible:
            return

        self._remember_foreground()
        self._position_popup()

        if self.mode == "preview":
            self._reset_input()

        self.popup.deiconify()
        self.popup.lift()

        try:
            self.popup.attributes("-topmost", True)
        except Exception:
            pass

        self.popup_visible = True

        # CoD2 can keep the keyboard focus even while our topmost window
        # is visible. Try a few short foreground handoffs while the popup
        # is being shown; the first successful one is enough.
        self.popup.after(20, self._focus_popup_for_typing)
        self.popup.after(80, self._focus_popup_for_typing)
        self.popup.after(160, self._focus_popup_for_typing)

    def hide_popup(self, clear: bool = False) -> None:
        if not self.popup_visible:
            return

        self.popup.withdraw()
        self.popup_visible = False

        if clear:
            self._reset_input()

        self.root.after(
            60,
            self._restore_foreground,
        )

    def toggle_popup(self) -> None:
        if self.popup_visible:
            self.hide_popup(clear=False)
        else:
            self.show_popup()

    def _reset_input(self) -> None:
        self.entry_var.set("")
        self.preview.configure(text="")
        self.hint.configure(
            text="Enter — перевести    Esc — закрыть"
        )
        self.entry.configure(state="normal")
        self.mode = "input"
        self.translation_in_progress = False

    def _on_escape(self, _event=None):
        self.hide_popup(clear=True)
        return "break"

    def _on_enter(self, _event=None):
        if self.translation_in_progress:
            return "break"

        if self.mode == "preview":
            self.hide_popup(clear=True)
            return "break"

        text = normalize_outgoing_text(
            self.entry_var.get()
        )

        if not text:
            self.preview.configure(
                text="Напиши сообщение.",
                fg="#ffbf69",
            )
            return "break"

        self.translation_in_progress = True

        self.preview.configure(
            text="Перевожу…",
            fg="#67d4ff",
        )
        self.hint.configure(
            text="Подожди, идёт перевод…"
        )
        self.entry.configure(state="disabled")

        threading.Thread(
            target=self._translate_worker,
            args=(text,),
            daemon=True,
            name="OutgoingTranslation",
        ).start()

        return "break"

    def _translate_worker(self, source: str) -> None:
        try:
            translated = translate_outgoing_text(
                source,
                TARGET_CODE,
            )
            self.events.put(
                (
                    "translation_ok",
                    (source, translated),
                )
            )
        except Exception as exc:
            self.events.put(
                (
                    "translation_error",
                    str(exc),
                )
            )

    def _show_translation(
        self,
        source: str,
        translated: str,
    ) -> None:
        self.translation_in_progress = False
        self.mode = "preview"
        self.last_translation = translated

        self.preview.configure(
            text=f"Перевод: {translated}",
            fg="#9de5a7",
        )

        self.hint.configure(
            text=(
                "ПРОТОТИП: в игру ничего не отправлено    "
                "Enter — закрыть    Esc — закрыть"
            )
        )

        self.last_var.set(
            f"Последний перевод: {source}  →  {translated}"
        )

        self.status_var.set(
            "Перевод готов. В CoD2 ничего не отправлено."
        )

    def _show_translation_error(
        self,
        error: str,
    ) -> None:
        self.translation_in_progress = False
        self.entry.configure(state="normal")

        self.preview.configure(
            text=f"Ошибка перевода: {error}",
            fg="#ff7676",
        )

        self.hint.configure(
            text="Enter — попробовать снова    Esc — закрыть"
        )

        try:
            self.entry.focus_force()
        except Exception:
            pass

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()

                if event == "toggle_popup":
                    self.toggle_popup()

                elif event == "hotkey_ready":
                    self.status_var.set(
                        "F9 готов. Можно свернуть это окно и зайти в CoD2."
                    )

                elif event == "hotkey_error":
                    self.status_var.set(str(payload))

                elif event == "translation_ok":
                    source, translated = payload
                    self._show_translation(
                        source,
                        translated,
                    )

                elif event == "translation_error":
                    self._show_translation_error(
                        str(payload)
                    )

        except queue.Empty:
            pass

        try:
            self.root.after(
                40,
                self._poll_events,
            )
        except tk.TclError:
            pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if tk is None or ttk is None:
        raise RuntimeError(
            "This prototype requires Tkinter and is intended for Windows."
        )

    app = OutgoingChatPrototype()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
