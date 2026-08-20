from __future__ import annotations

import ctypes
import os
import queue
import re
import threading
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
MAX_MESSAGE_CHARS = 160

WH_KEYBOARD_LL = 13
HC_ACTION = 0

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_BACK = 0x08
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_F9 = 0x78
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5

GWL_EXSTYLE = -20

WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = -1

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

GA_ROOT = 2


def normalize_outgoing_text(text: str) -> str:
    text = (text or "").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def translate_outgoing_text(
    text: str,
    target: str = TARGET_CODE,
) -> str:
    from deep_translator import GoogleTranslator

    source = normalize_outgoing_text(text)

    if not source:
        raise ValueError("Пустое сообщение")

    translated = GoogleTranslator(
        source="auto",
        target=target,
    ).translate(source)

    translated = normalize_outgoing_text(
        str(translated or "")
    )

    if not translated:
        raise RuntimeError(
            "Сервис перевода вернул пустой ответ"
        )

    return translated


def is_running_as_admin() -> bool:
    if os.name != "nt":
        return False

    try:
        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )
    except Exception:
        return False


class KeyboardCapture:
    """
    Low-level keyboard hook.

    В обычном режиме пропускает всё как есть.
    После F9 перехватывает key-down для нашего текста,
    но CoD2 остаётся foreground-приложением.
    """

    def __init__(self, events: queue.Queue) -> None:
        self.events = events
        self.active = False

        self.hook = None
        self.callback = None

        self.down_keys: set[int] = set()
        self.f9_down = False

    def set_active(self, value: bool) -> None:
        self.active = bool(value)

    def start(self) -> None:
        threading.Thread(
            target=self._run,
            daemon=True,
            name="OutgoingKeyboardHook",
        ).start()

    def _vk_to_text(
        self,
        user32,
        vk: int,
        scan_code: int,
    ) -> str:
        if vk in {
            VK_BACK,
            VK_RETURN,
            VK_ESCAPE,
            VK_F9,
            VK_SHIFT,
            VK_CONTROL,
            VK_MENU,
            VK_LCONTROL,
            VK_RCONTROL,
            VK_LMENU,
            VK_RMENU,
        }:
            return ""

        if any(
            key in self.down_keys
            for key in (
                VK_CONTROL,
                VK_LCONTROL,
                VK_RCONTROL,
                VK_MENU,
                VK_LMENU,
                VK_RMENU,
            )
        ):
            return ""

        state = (ctypes.c_ubyte * 256)()

        try:
            user32.GetKeyboardState(
                ctypes.byref(state)
            )
        except Exception:
            return ""

        for key in self.down_keys:
            if 0 <= key < 256:
                state[key] |= 0x80

        hwnd = int(
            user32.GetForegroundWindow() or 0
        )

        thread_id = 0
        if hwnd:
            thread_id = int(
                user32.GetWindowThreadProcessId(
                    wintypes.HWND(hwnd),
                    None,
                )
                or 0
            )

        layout = user32.GetKeyboardLayout(
            thread_id
        )

        buffer = ctypes.create_unicode_buffer(8)

        result = int(
            user32.ToUnicodeEx(
                vk,
                scan_code,
                ctypes.byref(state),
                buffer,
                len(buffer),
                0,
                layout,
            )
        )

        if result > 0:
            return "".join(
                buffer[index]
                for index in range(result)
            )

        if result < 0:
            # Сбрасываем состояние dead-key.
            user32.ToUnicodeEx(
                vk,
                scan_code,
                ctypes.byref(state),
                buffer,
                len(buffer),
                0,
                layout,
            )

        return ""

    def _run(self) -> None:
        if os.name != "nt":
            self.events.put(
                (
                    "hook_error",
                    "Keyboard hook работает только в Windows",
                )
            )
            return

        user32 = ctypes.WinDLL(
            "user32",
            use_last_error=True,
        )
        kernel32 = ctypes.WinDLL(
            "kernel32",
            use_last_error=True,
        )

        class KBDLLHOOKSTRUCT(
            ctypes.Structure
        ):
            _fields_ = [
                ("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                (
                    "dwExtraInfo",
                    ctypes.c_size_t,
                ),
            ]

        HOOKPROC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        user32.SetWindowsHookExW.restype = (
            ctypes.c_void_p
        )
        user32.CallNextHookEx.restype = (
            ctypes.c_ssize_t
        )

        kernel32.GetModuleHandleW.restype = (
            ctypes.c_void_p
        )

        user32.GetKeyboardLayout.restype = (
            ctypes.c_void_p
        )

        @HOOKPROC
        def hook_proc(
            n_code,
            w_param,
            l_param,
        ):
            if n_code != HC_ACTION:
                return user32.CallNextHookEx(
                    self.hook,
                    n_code,
                    w_param,
                    l_param,
                )

            data = ctypes.cast(
                l_param,
                ctypes.POINTER(
                    KBDLLHOOKSTRUCT
                ),
            ).contents

            vk = int(data.vkCode)
            scan = int(data.scanCode)
            message = int(w_param)

            key_down = message in (
                WM_KEYDOWN,
                WM_SYSKEYDOWN,
            )

            key_up = message in (
                WM_KEYUP,
                WM_SYSKEYUP,
            )

            if key_down:
                self.down_keys.add(vk)

            if key_up:
                self.down_keys.discard(vk)

            # F9 принадлежит нашему прототипу.
            if vk == VK_F9:
                if key_down:
                    if not self.f9_down:
                        self.f9_down = True
                        self.events.put(
                            (
                                "toggle_popup",
                                None,
                            )
                        )

                    return 1

                if key_up:
                    self.f9_down = False
                    return 1

            if not self.active:
                return user32.CallNextHookEx(
                    self.hook,
                    n_code,
                    w_param,
                    l_param,
                )

            # Key-up пропускаем.
            # Это снижает риск "залипшего"
            # W/Shift, если клавиша была
            # зажата перед F9.
            if key_up:
                return user32.CallNextHookEx(
                    self.hook,
                    n_code,
                    w_param,
                    l_param,
                )

            if not key_down:
                return 1

            if vk == VK_ESCAPE:
                self.events.put(
                    ("cancel", None)
                )
                return 1

            if vk == VK_RETURN:
                self.events.put(
                    ("submit", None)
                )
                return 1

            if vk == VK_BACK:
                self.events.put(
                    ("backspace", None)
                )
                return 1

            text = self._vk_to_text(
                user32,
                vk,
                scan,
            )

            if text:
                self.events.put(
                    ("text", text)
                )

            # Не отдаём key-down игре.
            return 1

        self.callback = hook_proc

        module = kernel32.GetModuleHandleW(
            None
        )

        self.hook = (
            user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                hook_proc,
                module,
                0,
            )
        )

        if not self.hook:
            error = ctypes.get_last_error()

            self.events.put(
                (
                    "hook_error",
                    (
                        "Не удалось установить "
                        f"keyboard hook: WinError {error}"
                    ),
                )
            )
            return

        self.events.put(
            ("hook_ready", None)
        )

        msg = wintypes.MSG()

        try:
            while (
                user32.GetMessageW(
                    ctypes.byref(msg),
                    None,
                    0,
                    0,
                )
                > 0
            ):
                user32.TranslateMessage(
                    ctypes.byref(msg)
                )
                user32.DispatchMessageW(
                    ctypes.byref(msg)
                )
        finally:
            if self.hook:
                user32.UnhookWindowsHookEx(
                    self.hook
                )
                self.hook = None


class OutgoingChatPrototype:
    def __init__(self) -> None:
        self.root = tk.Tk()

        self.root.title(APP_TITLE)
        self.root.geometry("550x300")
        self.root.minsize(520, 280)

        self.events: queue.Queue = (
            queue.Queue()
        )

        self.keyboard = KeyboardCapture(
            self.events
        )

        self.popup_visible = False
        self.translation_in_progress = (
            False
        )

        self.mode = "input"
        self.buffer = ""

        self.status_var = tk.StringVar(
            value="Запускаю keyboard hook…"
        )

        self.last_var = tk.StringVar(
            value="Последний перевод: —"
        )

        self._build_control_window()
        self._build_overlay_window()

        self.keyboard.start()

        self.root.after(
            30,
            self._poll_events,
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.root.destroy,
        )

    def _build_control_window(
        self,
    ) -> None:
        outer = ttk.Frame(
            self.root,
            padding=18,
        )

        outer.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            outer,
            text=(
                "Исходящий чат — "
                "no-focus prototype"
            ),
            font=(
                "Segoe UI",
                15,
                "bold",
            ),
        ).pack(anchor="w")

        ttk.Label(
            outer,
            text=(
                "Запускать ОТ ИМЕНИ "
                "АДМИНИСТРАТОРА. "
                "В CoD2 пока ничего "
                "не отправляется."
            ),
            foreground="#a33",
            wraplength=500,
        ).pack(
            anchor="w",
            pady=(6, 14),
        )

        box = ttk.LabelFrame(
            outer,
            text="Тест",
            padding=12,
        )

        box.pack(fill="x")

        ttk.Label(
            box,
            text=(
                "F9 — открыть строку "
                "без сворачивания CoD2"
            ),
        ).pack(anchor="w")

        ttk.Label(
            box,
            text=(
                "Печатай прямо в игре "
                "· Enter — перевод"
            ),
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Label(
            box,
            text=(
                "Esc или F9 — закрыть"
            ),
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Label(
            box,
            text=(
                "Для первого теста "
                "включи RU-раскладку "
                "до нажатия F9."
            ),
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Label(
            outer,
            textvariable=self.status_var,
            wraplength=500,
        ).pack(
            anchor="w",
            pady=(14, 0),
        )

        ttk.Label(
            outer,
            textvariable=self.last_var,
            wraplength=500,
        ).pack(
            anchor="w",
            pady=(8, 0),
        )

    def _build_overlay_window(
        self,
    ) -> None:
        popup = tk.Toplevel(
            self.root
        )

        popup.overrideredirect(True)
        popup.attributes(
            "-topmost",
            True,
        )

        popup.configure(
            bg="#101419"
        )

        width = 720
        height = 145

        screen_w = (
            popup.winfo_screenwidth()
        )

        screen_h = (
            popup.winfo_screenheight()
        )

        x = max(
            10,
            (screen_w - width) // 2,
        )

        y = max(
            10,
            int(screen_h * 0.70),
        )

        popup.geometry(
            f"{width}x{height}+{x}+{y}"
        )

        frame = tk.Frame(
            popup,
            bg="#101419",
            highlightthickness=1,
            highlightbackground=(
                "#424a55"
            ),
        )

        frame.pack(
            fill="both",
            expand=True,
        )

        header = tk.Frame(
            frame,
            bg="#101419",
        )

        header.pack(
            fill="x",
            padx=16,
            pady=(11, 6),
        )

        tk.Label(
            header,
            text="СООБЩЕНИЕ ВСЕМ",
            bg="#101419",
            fg="#f0f2f5",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(side="left")

        tk.Label(
            header,
            text=f"→ {TARGET_NAME}",
            bg="#101419",
            fg="#67d4ff",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(side="right")

        self.input_label = tk.Label(
            frame,
            text="",
            bg="#1c222a",
            fg="#ffffff",
            font=(
                "Segoe UI",
                13,
            ),
            anchor="w",
            padx=10,
            pady=9,
        )

        self.input_label.pack(
            fill="x",
            padx=16,
        )

        self.preview = tk.Label(
            frame,
            text="",
            bg="#101419",
            fg="#9de5a7",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            anchor="w",
        )

        self.preview.pack(
            fill="x",
            padx=16,
            pady=(7, 0),
        )

        self.hint = tk.Label(
            frame,
            text=(
                "Печатай прямо в игре · "
                "Enter — перевести · "
                "Esc/F9 — закрыть"
            ),
            bg="#101419",
            fg="#8f98a5",
            font=(
                "Segoe UI",
                9,
            ),
        )

        self.hint.pack(
            anchor="w",
            padx=16,
            pady=(6, 9),
        )

        # Создаём HWND заранее.
        popup.update_idletasks()

        self.popup = popup

        hwnd = int(
            popup.winfo_id()
        )

        if os.name == "nt":
            user32 = ctypes.WinDLL(
                "user32",
                use_last_error=True,
            )

            root_hwnd = int(
                user32.GetAncestor(
                    wintypes.HWND(hwnd),
                    GA_ROOT,
                )
                or hwnd
            )

            self.popup_hwnd = (
                root_hwnd
            )

            getter = getattr(
                user32,
                "GetWindowLongPtrW",
                user32.GetWindowLongW,
            )

            setter = getattr(
                user32,
                "SetWindowLongPtrW",
                user32.SetWindowLongW,
            )

            getter.restype = (
                ctypes.c_ssize_t
            )

            setter.restype = (
                ctypes.c_ssize_t
            )

            style = int(
                getter(
                    wintypes.HWND(
                        self.popup_hwnd
                    ),
                    GWL_EXSTYLE,
                )
            )

            style |= (
                WS_EX_LAYERED
                | WS_EX_NOACTIVATE
                | WS_EX_TOOLWINDOW
                | WS_EX_TRANSPARENT
            )

            setter(
                wintypes.HWND(
                    self.popup_hwnd
                ),
                GWL_EXSTYLE,
                style,
            )
        else:
            self.popup_hwnd = 0

        # Окно существует всегда,
        # но обычно полностью невидимо.
        popup.attributes(
            "-alpha",
            0.0,
        )

    def _show_overlay(self) -> None:
        self.popup.attributes(
            "-alpha",
            0.97,
        )

        if (
            os.name == "nt"
            and self.popup_hwnd
        ):
            ctypes.windll.user32.SetWindowPos(
                wintypes.HWND(
                    self.popup_hwnd
                ),
                wintypes.HWND(
                    HWND_TOPMOST
                ),
                0,
                0,
                0,
                0,
                (
                    SWP_NOMOVE
                    | SWP_NOSIZE
                    | SWP_NOACTIVATE
                ),
            )

    def _hide_overlay(self) -> None:
        self.popup.attributes(
            "-alpha",
            0.0,
        )

    def _render_buffer(self) -> None:
        if self.buffer:
            self.input_label.configure(
                text=(
                    self.buffer + "▌"
                ),
                fg="#ffffff",
            )
        else:
            self.input_label.configure(
                text=(
                    "Начинай печатать…"
                ),
                fg="#7f8996",
            )

    def show_popup(self) -> None:
        if self.popup_visible:
            return

        self.buffer = ""
        self.mode = "input"

        self.translation_in_progress = (
            False
        )

        self.preview.configure(
            text=""
        )

        self.hint.configure(
            text=(
                "Печатай прямо в игре · "
                "Enter — перевести · "
                "Esc/F9 — закрыть"
            )
        )

        self._render_buffer()

        self.keyboard.set_active(
            True
        )

        self.popup_visible = True
        self._show_overlay()

        self.status_var.set(
            (
                "F9: режим ввода активен. "
                "Foreground игры "
                "не переключаем."
            )
        )

    def hide_popup(
        self,
        status: str = "",
    ) -> None:
        if not self.popup_visible:
            return

        self.keyboard.set_active(
            False
        )

        self.popup_visible = False

        self.translation_in_progress = (
            False
        )

        self.mode = "input"

        self._hide_overlay()

        if status:
            self.status_var.set(
                status
            )

    def toggle_popup(self) -> None:
        if self.popup_visible:
            self.hide_popup(
                "F9: ввод закрыт."
            )
        else:
            self.show_popup()

    def append_text(
        self,
        value: str,
    ) -> None:
        if (
            not self.popup_visible
            or self.mode != "input"
            or self.translation_in_progress
        ):
            return

        remaining = (
            MAX_MESSAGE_CHARS
            - len(self.buffer)
        )

        if remaining <= 0:
            self.preview.configure(
                text=(
                    "Достигнут лимит "
                    f"{MAX_MESSAGE_CHARS} "
                    "символов."
                ),
                fg="#ffbf69",
            )
            return

        self.buffer += value[
            :remaining
        ]

        self._render_buffer()

    def backspace(self) -> None:
        if (
            self.popup_visible
            and self.mode == "input"
            and not self.translation_in_progress
            and self.buffer
        ):
            self.buffer = (
                self.buffer[:-1]
            )

            self._render_buffer()

    def submit(self) -> None:
        if (
            not self.popup_visible
            or self.translation_in_progress
        ):
            return

        if self.mode == "preview":
            self.hide_popup(
                (
                    "Перевод просмотрен. "
                    "В CoD2 ничего "
                    "не отправлено."
                )
            )
            return

        source = (
            normalize_outgoing_text(
                self.buffer
            )
        )

        if not source:
            self.preview.configure(
                text="Напиши сообщение.",
                fg="#ffbf69",
            )
            return

        self.translation_in_progress = (
            True
        )

        self.preview.configure(
            text="Перевожу…",
            fg="#67d4ff",
        )

        threading.Thread(
            target=self._translate_worker,
            args=(source,),
            daemon=True,
            name="OutgoingTranslation",
        ).start()

    def _translate_worker(
        self,
        source: str,
    ) -> None:
        try:
            translated = (
                translate_outgoing_text(
                    source,
                    TARGET_CODE,
                )
            )

            self.events.put(
                (
                    "translation_ok",
                    (
                        source,
                        translated,
                    ),
                )
            )

        except Exception as exc:
            self.events.put(
                (
                    "translation_error",
                    str(exc),
                )
            )

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = (
                    self.events.get_nowait()
                )

                if event == "toggle_popup":
                    self.toggle_popup()

                elif event == "text":
                    self.append_text(
                        str(payload)
                    )

                elif event == "backspace":
                    self.backspace()

                elif event == "submit":
                    self.submit()

                elif event == "cancel":
                    self.hide_popup(
                        "Esc: ввод отменён."
                    )

                elif event == "hook_ready":
                    if is_running_as_admin():
                        self.status_var.set(
                            (
                                "Hook готов. "
                                "Зайди в CoD2 "
                                "и нажми F9."
                            )
                        )
                    else:
                        self.status_var.set(
                            (
                                "Перезапусти "
                                "прототип ОТ ИМЕНИ "
                                "АДМИНИСТРАТОРА."
                            )
                        )

                elif event == "hook_error":
                    self.status_var.set(
                        str(payload)
                    )

                elif (
                    event
                    == "translation_ok"
                ):
                    source, translated = (
                        payload
                    )

                    if not self.popup_visible:
                        continue

                    self.translation_in_progress = (
                        False
                    )

                    self.mode = "preview"

                    self.preview.configure(
                        text=(
                            "Перевод: "
                            f"{translated}"
                        ),
                        fg="#9de5a7",
                    )

                    self.hint.configure(
                        text=(
                            "ПРОТОТИП: "
                            "в игру ничего "
                            "не отправлено · "
                            "Enter/Esc/F9 — закрыть"
                        )
                    )

                    self.last_var.set(
                        (
                            "Последний перевод: "
                            f"{source} → "
                            f"{translated}"
                        )
                    )

                elif (
                    event
                    == "translation_error"
                ):
                    self.translation_in_progress = (
                        False
                    )

                    self.preview.configure(
                        text=(
                            "Ошибка перевода: "
                            f"{payload}"
                        ),
                        fg="#ff7676",
                    )

        except queue.Empty:
            pass

        try:
            self.root.after(
                30,
                self._poll_events,
            )
        except tk.TclError:
            pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if tk is None:
        raise RuntimeError(
            "Tkinter required"
        )

    app = OutgoingChatPrototype()
    app.run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
