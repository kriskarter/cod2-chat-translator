"""Experimental CoD2 incoming-voice subtitle window.

No changes to the stable CoD2 Chat Translator, memory injection, DLL hooks,
microphone recording, or game assets. Only reads new voice.wav bytes.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import numpy as np

from voice_native_overlay import VoiceNativeOverlay
from voice_quality import evaluate_transcription, RecognitionQuality
from voice_vosk_ru import (
    MODEL_NAME as VOSK_RU_TEST,
    ensure_vosk_model, is_vosk_model, recognize_vosk, vosk_quality_reason,
)
from voice_capture_setup import ensure_voice_capture
from voice_nick_research import VoiceNickResearch
from voice_wire_cod2 import VoicePacketJournal, run_windows_packet_helper
from voice_packet_launcher import launch_elevated_packet_probe, disable_probe
from voice_cod2_names import read_cod2_client_names
from voice_screen_probe import (
    FrameThrottle, capture_if_game_foreground,
)
from voice_performance import asr_profile, capture_idle_seconds, discard_pending
from voice_game_window import (
    configure_overlay,
    find_cod2_window,
    is_cod2_foreground,
    is_cod2_running,
    make_cod2_borderless,
    raise_overlay,
)
from voice_engine import (
    AudioJob,
    BYTE_RATE,
    FileTail,
    LiveCollector,
    guess_voice_path,
    split_utterances,
    to_whisper_audio,
)

APP_NAME = "CoD2 Voice Prototype"
LIVE_POLL_SECONDS = 0.08
SUPPORTED_MODELS = ("tiny", "base", VOSK_RU_TEST)
SUPPORTED_TARGETS = {"Русский": "ru", "Українська": "uk", "English": "en"}


def app_data_folder() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home())
    else:
        base = Path(os.getenv("XDG_CACHE_HOME") or Path.home() / ".cache")
    folder = base / "CoD2VoicePrototype"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def read_recording(path: Path) -> bytes:
    """Accept CoD2 headerless raw files and conventional PCM WAV for tests."""
    if path.stat().st_size > 200 * 1024 * 1024:
        raise ValueError("Запись больше 200 МБ. Используй небольшой фрагмент.")
    with path.open("rb") as f:
        magic = f.read(12)
    if magic[:4] == b"RIFF" and magic[8:12] == b"WAVE":
        import wave
        with wave.open(str(path), "rb") as w:
            if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (1, 2, 8000):
                raise ValueError("Ожидается WAV PCM mono 16-bit 8000 Hz.")
            return w.readframes(w.getnframes())
    raw = path.read_bytes()
    if len(raw) % 2:
        raw = raw[:-1]
    return raw


def translate_text(text: str, source: str, target: str) -> tuple[str, str]:
    """Best-effort ONLINE text translation; recognition itself is offline."""
    if not text or source == target:
        return text, "local"
    import requests

    errors = []
    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": source or "auto", "tl": target, "dt": "t", "q": text},
            timeout=(0.6, 1.5),
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        result = "".join(
            str(segment[0]) for segment in response.json()[0]
            if isinstance(segment, list) and segment and segment[0]
        ).strip()
        if result and result.casefold() != text.strip().casefold():
            return result, "google"
        errors.append("Google: пустой/неизменённый ответ")
    except Exception as exc:
        errors.append("Google: " + type(exc).__name__)

    if source and source != "auto":
        try:
            response = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text[:400], "langpair": f"{source}|{target}"},
                timeout=(0.6, 1.5),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            payload = response.json()
            result = str(payload.get("responseData", {}).get("translatedText", "")).strip()
            if (
                result and result.casefold() != text.strip().casefold()
                and not result.casefold().startswith(("error", "'auto' is"))
            ):
                return result, "mymemory"
            errors.append("MyMemory: пустой/неизменённый ответ")
        except Exception as exc:
            errors.append("MyMemory: " + type(exc).__name__)
    return "", "; ".join(errors)


class VoiceStudio:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME + " — эксперимент")
        self.root.geometry("850x690")
        self.root.minsize(720, 560)

        self.events: queue.Queue = queue.Queue()
        self.jobs: queue.Queue[tuple[int, AudioJob, str, str, bool, bool]] = queue.Queue(maxsize=96)
        self.translations: queue.Queue = queue.Queue(maxsize=6)
        self.latest_displayed_seq = -1
        self.stop_flag = threading.Event()
        self.generation = 0
        self.seq = 0
        self.current_model_name = ""
        self.model = None

        self.path_var = tk.StringVar(value=str(guess_voice_path()))
        self.model_var = tk.StringVar(value="tiny")
        self.target_var = tk.StringVar(value="Русский")
        self.translate_var = tk.BooleanVar(value=True)
        self.fast_mode_var = tk.BooleanVar(value=True)
        self.overlay_var = tk.BooleanVar(value=True)
        # In-game subtitles must never intercept mouse clicks.
        self.move_overlay_var = tk.BooleanVar(value=False)
        self.save_var = tk.BooleanVar(value=False)
        self.auto_capture_var = tk.BooleanVar(value=True)
        self.nick_research_var = tk.BooleanVar(value=True)
        self.frame_capture_var = tk.BooleanVar(value=False)
        self.frame_capture_enabled = False  # thread-safe snapshot; no Tk access off UI thread
        self.frame_capture_queue: queue.Queue = queue.Queue(maxsize=2)
        self.frame_throttle = FrameThrottle(min_interval=2.0)
        self.nick_input_var = tk.StringVar(value="")
        self.packet_capture_var = tk.BooleanVar(value=False)
        self.packet_capture_enabled = False
        self.memory_names_var = tk.BooleanVar(value=False)
        self.memory_names_enabled = False
        self.packet_journal = None
        self.packet_stop_file = None
        self.live_game_root = None
        self.packet_status_var = tk.StringVar(
            value="ID говорящего: сбор UDP выключен (без изменения игры)."
        )
        self.capture_setup_var = tk.StringVar(value="Запись голоса: проверка настроек CoD2…")
        self._capture_deferred = False
        self.nick_research = None
        self.status_var = tk.StringVar(value="Готов. Выбери запись или запусти CoD2.")
        self.mode_var = tk.StringVar(value="Ожидание")
        self.count_var = tk.StringVar(value="Распознано: 0")
        self.count = 0

        self._build_ui()
        self.overlay = None
        self.native_overlay = None
        self._make_overlay()
        self._init_native_overlay()
        self._set_overlay_visibility()
        # Tk is only the editing/fallback surface; gameplay uses native Win32.
        self.root.after(200, self._apply_overlay_window_style)
        self.root.after(1200, self._keep_overlay_topmost)
        self.worker = threading.Thread(target=self._worker_loop, daemon=True, name="VoiceASRWorker")
        self.worker.start()
        self.translation_worker = threading.Thread(
            target=self._translate_loop, daemon=True, name="VoiceTranslationWorker"
        )
        self.translation_worker.start()
        self.frame_worker = threading.Thread(
            target=self._capture_frames_loop, daemon=True,
            name="CoD2SpeakerFrameEvidence",
        )
        self.frame_worker.start()
        self.root.after(100, self._pump_ui)
        self.root.after(700, self._prepare_capture)
        self.root.after(5000, self._retry_deferred_capture)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=15)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="CoD2 · голос → субтитры",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            outer, text="Эксперимент: распознавание локально, перевод через интернет при включённой опции.",
        ).pack(anchor="w", pady=(2, 12))

        source = ttk.LabelFrame(outer, text="Файл входящего голоса CoD2", padding=8)
        source.pack(fill="x")
        row = ttk.Frame(source)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.path_var).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="Выбрать", command=self.browse).pack(side="left", padx=(8, 0))
        ttk.Label(
            source,
            text="Обычно: D:\\SteamLibrary\\steamapps\\common\\Call of Duty 2\\voice.wav",
            foreground="#666",
        ).pack(anchor="w", pady=(4, 0))

        settings = ttk.Frame(outer)
        settings.pack(fill="x", pady=(12, 8))
        ttk.Label(settings, text="Распознавание:").pack(side="left")
        ttk.Combobox(
            settings, state="readonly", width=21, textvariable=self.model_var,
            values=SUPPORTED_MODELS,
        ).pack(side="left", padx=(6, 16))
        ttk.Label(settings, text="Перевод на:").pack(side="left")
        ttk.Combobox(
            settings, state="readonly", width=13, textvariable=self.target_var,
            values=list(SUPPORTED_TARGETS),
        ).pack(side="left", padx=(6, 0))
        ttk.Checkbutton(
            settings, text="Быстрый режим", variable=self.fast_mode_var
        ).pack(side="left", padx=(16, 0))

        opts = ttk.Frame(outer)
        opts.pack(fill="x")
        ttk.Checkbutton(opts, text="Переводить (онлайн)", variable=self.translate_var).pack(side="left")
        ttk.Checkbutton(
            opts, text="Оверлей", variable=self.overlay_var,
            command=self._set_overlay_visibility,
        ).pack(side="left", padx=(14, 0))
        ttk.Checkbutton(opts, text="Сохранять текстовый журнал", variable=self.save_var).pack(side="left", padx=(14, 0))
        ttk.Checkbutton(
            opts, text="Перемещать субтитры", variable=self.move_overlay_var,
            command=self._overlay_edit_changed,
        ).pack(side="left", padx=(14, 0))

        capture = ttk.Frame(outer)
        capture.pack(fill="x", pady=(7, 0))
        ttk.Checkbutton(
            capture, text="Автоматически включать запись голоса",
            variable=self.auto_capture_var, command=self._prepare_capture,
        ).pack(side="left")
        ttk.Checkbutton(
            capture, text="Исследовать ники (локально)",
            variable=self.nick_research_var, command=self._nick_research_changed,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            capture, text="Проверить настройки",
            command=self._prepare_capture,
        ).pack(side="right")
        ttk.Label(
            outer, textvariable=self.capture_setup_var, wraplength=740,
            foreground="#4a5568",
        ).pack(fill="x", anchor="w", pady=(3, 0))

        photo = ttk.Frame(outer)
        photo.pack(fill="x", pady=(5, 0))
        ttk.Checkbutton(
            photo,
            text="Сохранять игровые кадры с иконкой говорящего (эксперимент)",
            variable=self.frame_capture_var,
            command=self._frame_capture_changed,
        ).pack(side="left")
        ttk.Label(
            photo, text="Не более 12 кадров · только локально",
            foreground="#777",
        ).pack(side="left", padx=(10, 0))

        packetrow = ttk.Frame(outer)
        packetrow.pack(fill="x", pady=(5, 0))
        ttk.Checkbutton(
            packetrow, text="Получать ID говорящего из UDP (Windows UAC)",
            variable=self.packet_capture_var, command=self._packet_probe_changed,
        ).pack(side="left")
        ttk.Checkbutton(
            packetrow, text="Ники из памяти CoD2 1.3 (чтение)",
            variable=self.memory_names_var, command=self._memory_names_changed,
        ).pack(side="left", padx=(12, 0))
        ttk.Label(
            outer, textvariable=self.packet_status_var,
            foreground="#4a5568", wraplength=790,
        ).pack(fill="x", anchor="w", pady=(3, 0))

        nickrow = ttk.Frame(outer)
        nickrow.pack(fill="x", pady=(5, 0))
        ttk.Label(nickrow, text="Ник для последней реплики (если знаешь):").pack(side="left")
        ttk.Entry(nickrow, textvariable=self.nick_input_var, width=18).pack(
            side="left", padx=(6, 5)
        )
        ttk.Button(nickrow, text="Отметить", command=self.annotate_last_nick).pack(side="left")
        ttk.Button(
            nickrow, text="Открыть сведения о никах", command=self.open_nick_diagnostics,
        ).pack(side="right")

        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=(10, 7))
        self.live_btn = ttk.Button(btns, text="▶ Слушать игру", command=self.start_live)
        self.live_btn.pack(side="left")
        self.record_btn = ttk.Button(btns, text="▶ Проверить запись", command=self.start_replay)
        self.record_btn.pack(side="left", padx=8)
        self.stop_btn = ttk.Button(btns, text="■ Стоп", command=self.stop)
        self.stop_btn.pack(side="left")
        ttk.Button(
            btns, text="Оконный резерв",
            command=self.enable_cod2_borderless,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(btns, text="Очистить вывод", command=self._clear_log).pack(side="right")

        ttk.Label(outer, textvariable=self.status_var, wraplength=700).pack(fill="x", anchor="w")
        statrow = ttk.Frame(outer)
        statrow.pack(fill="x", pady=(4, 6))
        ttk.Label(statrow, textvariable=self.mode_var).pack(side="left")
        ttk.Label(statrow, textvariable=self.count_var).pack(side="right")

        self.output = scrolledtext.ScrolledText(
            outer, wrap="word", height=13, font=("Segoe UI", 10),
            state="disabled",
        )
        self.output.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="В Windows используется нативный Win32-оверлей из основного переводчика. "
                  "Если конкретный полноэкранный режим/драйвер скрывает его, "
                  "доступен «Оконный резерв» после /r_fullscreen 0 и /vid_restart. "
                  "Для переноса субтитров включи «Перемещать субтитры», затем выключи.",
            foreground="#777", wraplength=700,
        ).pack(anchor="w", pady=(8, 0))

    def _make_overlay(self):
        win = tk.Toplevel(self.root)
        win.title("CoD2 Voice Subtitle")
        win.overrideredirect(True)
        win.geometry("690x90+90+75")
        win.configure(bg="#111827")
        try:
            win.attributes("-topmost", True)
            win.attributes("-alpha", 0.90)
        except tk.TclError:
            pass
        frame = tk.Frame(win, bg="#111827", padx=12, pady=8)
        frame.pack(fill="both", expand=True)
        self.overlay_text = tk.Label(
            frame,
            text="🎙 CoD2 Voice — ожидание",
            bg="#111827", fg="#e5e7eb",
            font=("Segoe UI", 12), justify="left", anchor="w",
            wraplength=665,
        )
        self.overlay_text.pack(fill="both", expand=True)
        win.bind("<ButtonPress-1>", lambda e: self._start_drag(e))
        win.bind("<B1-Motion>", lambda e: self._drag(e))
        self.overlay = win

    def _init_native_overlay(self):
        if os.name != "nt":
            return
        try:
            # Identical native per-pixel-alpha drawing path to stable app.
            self.native_overlay = VoiceNativeOverlay(x=90, y=75)
            self.status_var.set(
                "Нативный Win32-оверлей включён. Проверяем поверх CoD2."
            )
        except Exception as exc:
            # Never prevent transcription when overlay initialization fails.
            self.native_overlay = None
            self.status_var.set(
                f"Нативный оверлей недоступен: {type(exc).__name__}: {exc}. "
                "Используется резервное Tk-окно."
            )

    def _overlay_edit_changed(self):
        # Native surface is click-through and cannot be dragged directly.
        # The Tk preview is only visible while repositioning the subtitles.
        if self.native_overlay is not None and not self.move_overlay_var.get():
            self.native_overlay.move(
                self.overlay.winfo_x(), self.overlay.winfo_y()
            )
        self._set_overlay_visibility()

    def _start_drag(self, event):
        if not self.move_overlay_var.get():
            return
        self._drag_origin = (
            event.x_root - self.overlay.winfo_x(),
            event.y_root - self.overlay.winfo_y(),
        )

    def _drag(self, event):
        if not self.move_overlay_var.get() or not hasattr(self, "_drag_origin"):
            return
        ox, oy = self._drag_origin
        self.overlay.geometry(f"+{event.x_root - ox}+{event.y_root - oy}")

    def _apply_overlay_window_style(self):
        if self.overlay is None or not self.overlay.winfo_exists():
            return
        if self.native_overlay is not None and not self.move_overlay_var.get():
            return
        if os.name == "nt":
            try:
                configure_overlay(
                    self.overlay,
                    click_through=not self.move_overlay_var.get(),
                )
            except Exception as exc:
                self.status_var.set(
                    f"Не удалось настроить оверлей: {type(exc).__name__}: {exc}"
                )

    def _keep_overlay_topmost(self):
        # Win32 raises it without activating/focusing the game overlay.
        # Does not circumvent exclusive fullscreen; borderless is required.
        if self.overlay is not None and self.overlay_var.get() and os.name == "nt":
            try:
                if self.native_overlay is not None and not self.move_overlay_var.get():
                    self.native_overlay.force_topmost()
                else:
                    raise_overlay(self.overlay)
            except Exception:
                pass
        if self.root.winfo_exists():
            self.root.after(1500, self._keep_overlay_topmost)

    def enable_cod2_borderless(self):
        if os.name != "nt":
            self.status_var.set("Режим CoD2 → поверх доступен только в Windows.")
            return
        hwnd = find_cod2_window()
        if not hwnd:
            self.status_var.set(
                "Окно CoD2 Multiplayer не найдено. Запусти игру."
            )
            return
        ok, detail = make_cod2_borderless(hwnd)
        if not ok:
            self.status_var.set(detail)
            messagebox.showinfo(
                "CoD2 · субтитры поверх игры",
                detail + "\n\n"
                "В игре: консоль (~) → /r_fullscreen 0 → Enter, "
                "затем /vid_restart → Enter. "
                "После перезапуска изображения нажми эту кнопку снова.",
            )
            return
        self.overlay_var.set(True)
        self._set_overlay_visibility()
        self._apply_overlay_window_style()
        raise_overlay(self.overlay)
        self.status_var.set(detail + ". Субтитры подняты поверх окна игры.")

    def _set_overlay_visibility(self):
        if self.overlay is None:
            return
        if not self.overlay_var.get():
            self.overlay.withdraw()
            if self.native_overlay is not None:
                self.native_overlay.hide()
            return

        if self.native_overlay is not None:
            if self.move_overlay_var.get():
                self.native_overlay.hide()
                self.overlay.deiconify()
                self.overlay.attributes("-topmost", True)
                self.root.after(60, self._apply_overlay_window_style)
            else:
                self.overlay.withdraw()
                self.native_overlay.show()
            return

        # Last-resort Tk fallback when native Win32 initialization fails.
        self.overlay.deiconify()
        self.overlay.attributes("-topmost", True)
        self.root.after(60, self._apply_overlay_window_style)

    def browse(self):
        filename = filedialog.askopenfilename(
            title="Найти voice.wav", filetypes=[("WAV / raw PCM", "*.wav"), ("Все файлы", "*.*")]
        )
        if filename:
            self.path_var.set(filename)
            self._prepare_capture()

    def _prepare_capture(self):
        if not self.auto_capture_var.get():
            self.capture_setup_var.set(
                "Автоматическая настройка выключена. Запись требует winvoice_save_voice 1."
            )
            self._capture_deferred = False
            return
        path = Path(self.path_var.get().strip())
        # Never touch configs for a sample like voice(3).wav in Downloads.
        if path.name.casefold() != "voice.wav":
            self.capture_setup_var.set(
                "Для автоматической настройки выбери voice.wav в корне папки игры."
            )
            self._capture_deferred = False
            return
        running = is_cod2_running()
        summary = ensure_voice_capture(
            path, game_running=running,
            include_logfile=self.nick_research_var.get(),
        )
        self._capture_deferred = summary.deferred > 0
        if summary.found == 0:
            message = "Не найдены игровые config_mp.cfg; проверь путь к CoD2 и профиль."
        elif summary.failed:
            message = (
                f"Настройки CoD2: ошибок {summary.failed}/{summary.found}. "
                f"{summary.error}"
            )
        elif summary.deferred:
            message = (
                f"Найдено профилей: {summary.found}. Игра уже запущена: "
                "изменения будут применены после её закрытия. "
                "Для включения прямо сейчас: /seta winvoice_save_voice 1 "
                + (", /seta logfile 2" if self.nick_research_var.get() else "")
            )
        else:
            message = (
                f"Запись голоса настроена в {summary.ready} профилях "
                f"(изменено {summary.changed}, резервные копии .cod2voice.bak). "
                "Если игра уже была запущена, нужна следующая загрузка игры."
            )
        self.capture_setup_var.set(message)

    def _retry_deferred_capture(self):
        if self._capture_deferred and self.auto_capture_var.get():
            self._prepare_capture()
        if self.root.winfo_exists():
            self.root.after(5000, self._retry_deferred_capture)

    def _packet_probe_changed(self):
        if not self.packet_capture_var.get():
            self.packet_capture_enabled = False
            if self.packet_stop_file is not None:
                try:
                    disable_probe(self.packet_stop_file)
                except OSError:
                    pass
            self.packet_journal = None
            self.packet_status_var.set("ID говорящего: сетевой сбор отключён.")
            return
        allowed = messagebox.askyesno(
            "CoD2 · пассивные пакеты голосового чата",
            "В CoD2 1.3 сервер передаёт номер говорящего в UDP-пакетах. "
            "Разрешить отдельному процессу Windows наблюдать входящие UDP-пакеты?\n\n"
            "Windows попросит права администратора (UAC). "
            "Аудио и содержимое сетевых пакетов не сохраняются; в локальном "
            "журнале остаются только времена и номера игроков.\n\n"
            "Обычная игра не изменяется. Некоторые античиты могут ограничивать "
            "сетевые диагностические инструменты. По умолчанию функция выключена.",
        )
        if not allowed:
            self.packet_capture_var.set(False)
            return
        journal = app_data_folder() / f"voice_packet_probe_{os.getpid()}_{time.time_ns()}.jsonl"
        stopfile = journal.with_suffix(".stop")
        try:
            stopfile.unlink(missing_ok=True)
            self.packet_journal = VoicePacketJournal(journal)
            result = launch_elevated_packet_probe(
                parent_pid=os.getpid(), journal_path=journal, stop_path=stopfile,
            )
            if not result.ok:
                self.packet_capture_var.set(False)
                self.packet_journal = None
                self.packet_status_var.set(result.message)
                return
            self.packet_capture_enabled = True
            self.packet_stop_file = stopfile
            self.packet_status_var.set(result.message)
        except (OSError, ValueError) as exc:
            self.packet_capture_var.set(False)
            self.packet_capture_enabled = False
            self.packet_journal = None
            self.packet_status_var.set(
                "Невозможно запустить сетевую диагностику: " + type(exc).__name__
            )

    def _memory_names_changed(self):
        if not self.memory_names_var.get():
            self.memory_names_enabled = False
            return
        allowed = messagebox.askyesno(
            "CoD2 1.3 · чтение ников",
            "Для сопоставления ID с ником будет выполняться ЧТЕНИЕ небольшой "
            "таблицы игроков из работающего CoD2MP_s.exe.\n\n"
            "Адрес таблицы получен из открытого проекта CoD2x и проверяется "
            "по структуре; в другой сборке игры может не работать.\n\n"
            "Программа никогда не записывает в память игры и не внедряет DLL. "
            "Некоторые античиты могут реагировать даже на чтение памяти. "
            "Используй только в тестовой сессии без античита. Включить?",
        )
        if not allowed:
            self.memory_names_var.set(False)
            return
        self.memory_names_enabled = True
        self.packet_status_var.set(
            "Чтение ников разрешено для теста CoD2 1.3. "
            "Ники появятся только при доказанном ID говорящего."
        )

    def _frame_capture_changed(self):
        if self.frame_capture_var.get():
            consent = messagebox.askyesno(
                "Снимки говорящего в CoD2",
                "Для эксперимента программа будет сохранять до 12 "
                "снимков экрана, когда обнаружит голос игрока.\n\n"
                "Снимки могут содержать сообщения чата и другую информацию "
                "с экрана. Они остаются только на компьютере в папке "
                "%LOCALAPPDATA%\\CoD2VoicePrototype\\speaker_frames.\n\n"
                "Разрешить сохранение снимков?",
            )
            if not consent:
                self.frame_capture_var.set(False)
                return
            if not self.nick_research_var.get():
                self.nick_research_var.set(True)
                self._nick_research_changed()
            self.frame_capture_enabled = True
            self.status_var.set(
                "Сбор кадров разрешён. Окно CoD2 должно быть активным."
            )
        else:
            self.frame_capture_enabled = False
            self.status_var.set("Сбор снимков говорящих выключен.")

    def _queue_speaker_frame(self, gen: int):
        if (
            gen != self.generation
            or not self.frame_capture_enabled
            or self.nick_research is None
            or not self.frame_throttle.allow()
        ):
            return
        name = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            self.frame_capture_queue.put_nowait(
                (gen, self.seq + 1, name, self.nick_research)
            )
        except queue.Full:
            pass  # never block voice capture due to screenshots

    def _capture_frames_loop(self):
        while True:
            gen, hint, label, research = self.frame_capture_queue.get()
            try:
                if gen != self.generation or not self.frame_capture_enabled:
                    continue
                # Give the game's speaking icon time to appear, outside the
                # STT / voice-file watcher thread.
                time.sleep(0.18)
                if gen != self.generation or not self.frame_capture_enabled:
                    continue
                quality, path = capture_if_game_foreground(
                    app_data_folder() / "speaker_frames",
                    label,
                    is_cod2_foreground,
                )
                research.record_screen_frame(
                    seq_hint=hint,
                    file_name=path.name if path else None,
                    quality=quality,
                )
                if path:
                    self.events.put((
                        "frame_saved", gen,
                        "Игровой кадр сохранён для исследования ника: " + path.name,
                    ))
                elif quality != "game_not_foreground":
                    self.events.put((
                        "frame_saved", gen,
                        "Игровой кадр не получен: " + quality,
                    ))
            except (OSError, ValueError) as exc:
                self.events.put((
                    "frame_saved", gen,
                    "Ошибка снимка для проверки ника: " + type(exc).__name__,
                ))
            finally:
                self.frame_capture_queue.task_done()

    def _nick_research_changed(self):
        # Toggling local diagnostic collection off must take effect immediately,
        # even if the user does not restart live transcription.
        if not self.nick_research_var.get():
            self.nick_research = None
            self.frame_capture_var.set(False)
            self.frame_capture_enabled = False
        elif self.mode_var.get() == "Режим: живая CoD2":
            path = Path(self.path_var.get().strip())
            self.nick_research = VoiceNickResearch(
                path, app_data_folder() / "voice_nickname_research.jsonl"
            )
        self._prepare_capture()

    def annotate_last_nick(self):
        if self.nick_research is None:
            self.status_var.set("Включи «Исследовать ники» и «Слушать игру».")
            return
        if self.nick_research.annotate(self.nick_input_var.get()):
            self.status_var.set("Пометка последней реплики сохранена локально.")
            self.nick_input_var.set("")
        else:
            self.status_var.set("Сначала дождись реплики и введи ник игрока.")

    def open_nick_diagnostics(self):
        folder = app_data_folder()
        if os.name == "nt":
            os.startfile(str(folder))
        else:
            self.status_var.set("Папка диагностики: " + str(folder))

    def _clear_log(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.count = 0
        self.count_var.set("Распознано: 0")

    def _write_log(self, message: str):
        self.output.configure(state="normal")
        self.output.insert("end", datetime.now().strftime("%H:%M:%S") + "  " + message + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _start_session(self):
        self.stop()
        self.stop_flag = threading.Event()
        return self.generation, self.stop_flag

    def start_live(self):
        path = Path(self.path_var.get().strip())
        if not str(path):
            return
        self._prepare_capture()
        self.live_game_root = path.parent
        gen, flag = self._start_session()
        self.nick_research = (
            VoiceNickResearch(
                path, app_data_folder() / "voice_nickname_research.jsonl"
            ) if self.nick_research_var.get() else None
        )
        self._preload_model(gen, self.model_var.get(), self.fast_mode_var.get())
        self.mode_var.set("Режим: живая CoD2")
        self.status_var.set("Ожидаю новые байты в voice.wav (старые пропускаются).")
        threading.Thread(
            target=self._live_loop,
            args=(gen, flag, path, self.model_var.get(), SUPPORTED_TARGETS[self.target_var.get()], self.translate_var.get(), self.fast_mode_var.get()),
            daemon=True,
            name="VoiceFileTail",
        ).start()

    def start_replay(self):
        self.nick_research = None
        path = Path(self.path_var.get().strip())
        if not path.is_file():
            messagebox.showwarning(APP_NAME, "Выбери существующий voice.wav с записью.")
            return
        gen, flag = self._start_session()
        self.mode_var.set("Режим: запись")
        self.status_var.set("Разбиваю запись на голосовые фрагменты…")
        threading.Thread(
            target=self._replay_loop,
            args=(gen, flag, path, self.model_var.get(), SUPPORTED_TARGETS[self.target_var.get()], self.translate_var.get(), self.fast_mode_var.get()),
            daemon=True,
            name="VoiceFileReplay",
        ).start()

    def stop(self):
        if hasattr(self, "stop_flag"):
            self.stop_flag.set()
        self.generation += 1
        self.latest_displayed_seq = -1
        try:
            while True:
                self.jobs.get_nowait()
                self.jobs.task_done()
        except queue.Empty:
            pass
        try:
            while True:
                self.translations.get_nowait()
                self.translations.task_done()
        except queue.Empty:
            pass
        if hasattr(self, "mode_var"):
            self.mode_var.set("Остановлено")

    def _preload_model(self, gen: int, model: str, fast: bool):
        """Warm selected speech-recognition model before voice arrives."""
        self.jobs.put_nowait((gen, AudioJob(0, b"", "preload"), model, "", False, fast))

    def _enqueue(
        self, gen: int, raw: bytes, origin: str, model: str,
        target: str, translate: bool, fast: bool,
        started_at: float | None = None, finished_at: float | None = None,
    ):
        if gen != self.generation:
            return
        slot = None
        name = None
        evidence = "network_probe_off"
        journal = self.packet_journal
        if (
            origin == "live" and started_at is not None
            and finished_at is not None and self.packet_capture_enabled
            and journal is not None
        ):
            slot, evidence = journal.match(started_at, finished_at)
            if slot is not None and self.memory_names_enabled:
                checked = read_cod2_client_names(
                    self.live_game_root or Path("")
                )
                name = checked.slots.get(slot)
                evidence += "|" + checked.state
        label = (
            name if name is not None
            else f"Игрок #{slot} (ник неизвестен)" if slot is not None
            else "Игрок (ник неизвестен)"
        )
        # Tiny packets usually represent mic-clicks, not a spoken phrase.
        for piece in split_utterances(raw):
            self.seq += 1
            item = (
                gen, AudioJob(
                    self.seq, piece, origin, speaker_slot=slot,
                    speaker_label=label, speaker_evidence=evidence,
                ), model, target, translate, fast,
            )
            if origin == "live" and self.nick_research is not None:
                try:
                    self.nick_research.observe(
                        seq=self.seq,
                        seconds=len(piece) / BYTE_RATE,
                        origin=origin, speaker_slot=slot,
                        speaker_name=name, speaker_method=evidence,
                    )
                except (OSError, ValueError) as exc:
                    self.events.put((
                        "status", gen,
                        "Диагностика ника недоступна: " + str(exc)
                    ))
            if origin == "live":
                # Keep one *pending* live phrase, not a long backlog of stale
                # commands. The running STT cannot be preempted.
                dropped = discard_pending(self.jobs)
                if dropped:
                    self.events.put(("status", gen, (
                        f"Свежая реплика: пропущено старых из очереди: {dropped}."
                    )))
            try:
                self.jobs.put_nowait(item)
            except queue.Full:
                self.events.put(("status", gen, "Очередь заполнена — пропущена часть речи."))
                break

    def _live_loop(self, gen, stop_flag, path, model, target, translate, fast):
        tail = FileTail(path)
        collector = LiveCollector(idle_seconds=capture_idle_seconds(fast))
        previous_offset = None
        last_notice = 0.0
        speech_started = None
        previous_probe_status = None
        while not stop_flag.is_set():
            journal = self.packet_journal
            if journal is not None:
                journal.poll()
                if journal.status != previous_probe_status:
                    previous_probe_status = journal.status
                    self.events.put((
                        "packet_status", gen,
                        "UDP-диагностика CoD2: " + journal.status,
                    ))
            if not path.exists() and time.monotonic() - last_notice > 5:
                self.events.put(("status", gen, "Жду создания файла: " + str(path)))
                last_notice = time.monotonic()
            data = tail.read_new()
            if previous_offset is not None and tail.offset is not None and tail.offset < previous_offset:
                collector.reset()
                speech_started = None
            previous_offset = tail.offset
            if data:
                now = time.monotonic()
                if not collector.buffer and speech_started is None:
                    speech_started = now
                    self._queue_speaker_frame(gen)
                for complete in collector.feed(data, now=now):
                    self._enqueue(
                        gen, complete, "live", model, target, translate, fast,
                        started_at=speech_started or now, finished_at=now,
                    )
                    speech_started = now
            else:
                now = time.monotonic()
                complete = collector.flush_if_idle(now=now)
                if complete is not None:
                    self._enqueue(
                        gen, complete, "live", model, target, translate, fast,
                        started_at=speech_started or now, finished_at=now,
                    )
                    speech_started = None
            stop_flag.wait(LIVE_POLL_SECONDS)
        # Do not enqueue partial stale speech after Stop.

    def _replay_loop(self, gen, stop_flag, path, model, target, translate, fast):
        try:
            raw = read_recording(path)
            clips = split_utterances(raw)
            self.events.put(("status", gen, f"Найдено {len(clips)} фрагментов / {len(raw) / BYTE_RATE:.1f} с записи."))
            for i, clip in enumerate(clips, 1):
                if stop_flag.is_set() or gen != self.generation:
                    break
                # A bounded queue prevents a long sample from exhausting RAM.
                while self.jobs.qsize() >= 32 and not stop_flag.wait(.15):
                    pass
                if stop_flag.is_set():
                    break
                self.seq += 1
                self.jobs.put((gen, AudioJob(self.seq, clip, f"recording {i}/{len(clips)}"), model, target, translate, fast))
        except Exception as exc:
            self.events.put(("status", gen, f"Ошибка чтения записи: {type(exc).__name__}: {exc}"))

    def _worker_loop(self):
        while True:
            gen, job, model_name, target, do_translate, fast = self.jobs.get()
            try:
                if gen != self.generation:
                    continue
                queue_seconds = max(0.0, time.monotonic() - job.queued_at)
                model_seconds = 0.0
                if self.model is None or self.current_model_name != model_name:
                    loading = time.perf_counter()
                    if is_vosk_model(model_name):
                        self.events.put(("status", gen, (
                            "Загружаю Vosk RU (русский язык; тест скорости)…"
                        )))
                        path = ensure_vosk_model(
                            app_data_folder() / "vosk_models",
                            status=lambda message: self.events.put(
                                ("status", gen, message)
                            ),
                        )
                        from vosk import Model, SetLogLevel
                        SetLogLevel(-1)
                        self.model = Model(str(path))
                    else:
                        self.events.put(("status", gen, (
                            f"Загружаю Whisper {model_name} "
                            "(при первом запуске скачивается модель)…"
                        )))
                        from faster_whisper import WhisperModel
                        self.model = WhisperModel(
                            model_name, device="cpu", compute_type="int8",
                            cpu_threads=max(1, min(4, os.cpu_count() or 2)),
                            download_root=str(app_data_folder() / "models"),
                        )
                    self.current_model_name = model_name
                    model_seconds = time.perf_counter() - loading
                if job.origin == "preload":
                    self.events.put(("status", gen, (
                        f"{model_name} готов ({model_seconds:.1f} с). "
                        "Ожидаю новых голосовых сообщений."
                    )))
                    continue
                mode_label = "Vosk RU" if is_vosk_model(model_name) else "Whisper"
                self.events.put((
                    "status", gen, f"{mode_label}: распознаю фрагмент {job.seq}…"
                ))
                inference_start = time.perf_counter()
                seconds = len(job.raw_pcm) / BYTE_RATE
                if is_vosk_model(model_name):
                    recognized = recognize_vosk(self.model, job.raw_pcm)
                    # Russian is selected by user, NOT automatically detected.
                    language = "ru"
                    probability = None  # Vosk does not provide Whisper language score.
                    reason = vosk_quality_reason(recognized)
                    verdict = RecognitionQuality(
                        trustworthy=reason is None, reason=reason or ""
                    )
                else:
                    samples = to_whisper_audio(job.raw_pcm)
                    pieces, info = self.model.transcribe(
                        samples, language=None, **asr_profile(fast),
                    )
                    pieces = list(pieces)  # inference occurs during iteration
                    recognized = " ".join(
                        segment.text.strip() for segment in pieces if segment.text.strip()
                    ).strip()
                    language = str(info.language or "auto")
                    probability = float(
                        getattr(info, "language_probability", 0.0) or 0.0
                    )
                    verdict = evaluate_transcription(
                        recognized, language, probability, pieces, seconds
                    )
                asr_seconds = time.perf_counter() - inference_start
                timings = {
                    "queue_seconds": queue_seconds,
                    "model_seconds": model_seconds,
                    "asr_seconds": asr_seconds,
                    "total_seconds": max(
                        0.0, time.monotonic() - job.queued_at
                    ),
                    "engine": mode_label,
                }
                if not verdict.trustworthy:
                    if gen == self.generation:
                        self.events.put(("uncertain", gen, {
                            "language": language,
                            "probability": probability,
                            "text": recognized,
                            "reason": verdict.reason,
                            "seconds": seconds,
                            "speaker_label": job.speaker_label,
                            "speaker_slot": job.speaker_slot,
                            "speaker_evidence": job.speaker_evidence,
                            **timings,
                        }))
                    continue
                waiting_translation = bool(do_translate and language != target)
                # Show the recognized original immediately: network translation
                # must not block the only CPU Whisper worker.
                if gen == self.generation:
                    self.events.put(("result", gen, {
                        "seq": job.seq,
                        "language": language,
                        "probability": probability,
                        "tentative": verdict.tentative,
                        "text": recognized,
                        "translation": "",
                        "provider": "pending" if waiting_translation else "off",
                        "origin": job.origin,
                        "seconds": seconds,
                        "speaker_label": job.speaker_label,
                        "speaker_slot": job.speaker_slot,
                        "speaker_evidence": job.speaker_evidence,
                        **timings,
                    }))
                if waiting_translation and gen == self.generation:
                    discard_pending(self.translations, max_pending=1)
                    try:
                        self.translations.put_nowait(
                            (
                                gen, job.seq, recognized, language, target,
                                job.queued_at, job.speaker_label,
                                verdict.tentative,
                            )
                        )
                    except queue.Full:
                        self.events.put(("status", gen, "Очередь онлайн-перевода заполнена."))
            except Exception as exc:
                self.events.put(("status", gen, f"Ошибка распознавания: {type(exc).__name__}: {exc}"))
            finally:
                self.jobs.task_done()

    def _translate_loop(self):
        """Network calls run independently of CPU speech recognition."""
        while True:
            gen, seq, original, language, target, queued_at, speaker_label, tentative = self.translations.get()
            try:
                if gen != self.generation:
                    continue
                start = time.perf_counter()
                translated, provider = translate_text(original, language, target)
                self.events.put(("translation", gen, {
                    "seq": seq,
                    "original": original,
                    "language": language,
                    "tentative": tentative,
                    "translation": translated,
                    "provider": provider,
                    "network_seconds": time.perf_counter() - start,
                    "total_seconds": max(0.0, time.monotonic() - queued_at),
                    "speaker_label": speaker_label,
                }))
            except Exception as exc:
                self.events.put(("status", gen, f"Ошибка онлайн-перевода: {type(exc).__name__}: {exc}"))
            finally:
                self.translations.task_done()

    def _pump_ui(self):
        try:
            for _ in range(50):
                event_type, gen, payload = self.events.get_nowait()
                if gen != self.generation:
                    continue
                if event_type == "status":
                    self.status_var.set(payload)
                elif event_type == "packet_status":
                    self.packet_status_var.set(str(payload))
                    self._write_log(str(payload))
                elif event_type == "frame_saved":
                    self._write_log("📷 " + str(payload))
                elif event_type == "uncertain":
                    self.status_var.set(
                        f"Сомнительная речь ({payload['seconds']:.1f} с) — не переводил."
                    )
                    self._write_log(
                        f"⚠ Пропущено: {payload['reason']}. "
                        f"Черновик: {payload['text'] or 'нет текста'} "
                        f"[очередь {payload['queue_seconds']:.1f}с; "
                        f"{payload['engine']} {payload['asr_seconds']:.1f}с]"
                    )
                elif event_type == "translation":
                    if payload["translation"]:
                        self._write_log(
                            f"    → {payload['translation']} [{payload['provider']}] "
                            f"[сеть {payload['network_seconds']:.1f}с; "
                            f"всего {payload['total_seconds']:.1f}с]"
                        )
                    else:
                        self._write_log(
                            f"    ↳ Перевод недоступен ({payload['provider']}) "
                            f"[сеть {payload['network_seconds']:.1f}с]"
                        )
                    # A delayed HTTP response must never overwrite subtitles
                    # from a more recent player utterance.
                    if payload["seq"] == self.latest_displayed_seq:
                        if payload["translation"]:
                            if self.overlay is not None:
                                self.overlay_text.configure(
                                    text=f"🎙 {payload['speaker_label']} · "
                                         f"{payload['language'].upper()}: "
                                         f"{'⚠ Предварительно: ' if payload.get('tentative') else ''}"
                                         f"{payload['original']}\n→ {payload['translation']}"
                                )
                            if self.native_overlay is not None:
                                self.native_overlay.update(
                                    language=payload["language"].upper(),
                                    original=("⚠ " if payload.get("tentative") else "") + payload["original"],
                                    translated=payload["translation"],
                                    nickname=payload["speaker_label"],
                                )
                        self.status_var.set(
                            f"Перевод: сеть {payload['network_seconds']:.1f} с; "
                            f"от захвата до перевода {payload['total_seconds']:.1f} с"
                        )
                elif event_type == "result":
                    self.count += 1
                    self.count_var.set(f"Распознано: {self.count}")
                    lang = (
                        f"{payload['language'].upper()} "
                        f"({payload['probability']:.0%})"
                        if payload['probability'] is not None
                        else "RU (Vosk · язык задан вручную)"
                    )
                    if payload.get("tentative"):
                        lang += " · предварительно"
                    msg = (
                        f"🎙 {payload['speaker_label']} "
                        f"[{lang}] {payload['text']}"
                    )
                    if payload["provider"] == "pending":
                        msg += "\n    ↳ Перевод запрошен (без блокировки Whisper)."
                    msg += (
                        f" [очередь {payload['queue_seconds']:.1f}с; "
                        f"{payload['engine']} {payload['asr_seconds']:.1f}с; "
                        f"модель {payload['model_seconds']:.1f}с]"
                    )
                    self._write_log(msg)
                    self.status_var.set(
                        f"{'Предварительно' if payload.get('tentative') else 'Распознано'}: "
                        f"{payload['engine']} {payload['asr_seconds']:.1f} с; "
                        f"очередь {payload['queue_seconds']:.1f} с; "
                        f"загрузка модели {payload['model_seconds']:.1f} с"
                    )
                    self.latest_displayed_seq = payload["seq"]
                    if self.overlay is not None:
                        display = (
                            f"🎙 {payload['speaker_label']} · "
                            f"{payload['language'].upper()}: "
                            f"{'⚠ Предварительно: ' if payload.get('tentative') else ''}"
                            f"{payload['text']}"
                        )
                        if payload["translation"]:
                            display += "\n→ " + payload["translation"]
                        self.overlay_text.configure(text=display)
                    if self.native_overlay is not None:
                        try:
                            self.native_overlay.update(
                                language=payload["language"].upper(),
                                original=("⚠ " if payload.get("tentative") else "") + payload["text"],
                                translated=payload["translation"],
                                nickname=payload["speaker_label"],
                            )
                        except Exception as exc:
                            self.status_var.set(
                                f"Ошибка нативных субтитров: {type(exc).__name__}: {exc}"
                            )
                    if self.save_var.get():
                        with (app_data_folder() / "transcripts.jsonl").open("a", encoding="utf-8") as f:
                            f.write(json.dumps(
                                {"time": datetime.now().isoformat(timespec="seconds"), **payload},
                                ensure_ascii=False,
                            ) + "\n")
        except queue.Empty:
            pass
        except Exception as exc:
            self.status_var.set(f"Ошибка интерфейса: {exc}")
        finally:
            self.root.after(100, self._pump_ui)

    def close(self):
        if self.packet_stop_file is not None:
            try:
                disable_probe(self.packet_stop_file)
            except OSError:
                pass
        self.stop()
        if self.native_overlay is not None:
            try:
                self.native_overlay.destroy()
            except Exception:
                pass
            self.native_overlay = None
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass
    VoiceStudio(root)
    root.mainloop()


if __name__ == "__main__":
    if "--cod2-voice-probe" in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument("--cod2-voice-probe", action="store_true")
        parser.add_argument("--parent-pid", type=int, required=True)
        parser.add_argument("--journal", type=Path, required=True)
        parser.add_argument("--stop-file", type=Path, required=True)
        args = parser.parse_args()
        sys.exit(run_windows_packet_helper(
            args.parent_pid, args.journal, args.stop_file
        ))
    else:
        main()
