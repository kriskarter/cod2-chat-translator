from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # pragma: no cover
    tk = None
    messagebox = ttk = None


def no_window_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def localized(lang: str, ru: str, en: str, uk: str | None = None) -> str:
    if lang == "uk":
        return uk if uk is not None else en
    return ru if lang == "ru" else en


class ProgressUI:
    """Small localized updater window. It is best-effort and never blocks the update logic."""

    def __init__(self, lang: str) -> None:
        self.lang = lang if lang in {"ru", "uk", "en"} else "ru"
        self.root = None
        self.status = None
        self.detail = None
        self.bar = None
        if not (tk and ttk):
            return
        try:
            root = tk.Tk()
            root.title("CoD2 Chat Translator — " + localized(self.lang, "Обновление", "Update", "Оновлення"))
            root.resizable(False, False)
            try:
                root.iconbitmap(default=str(Path(sys.executable).resolve()))
            except Exception:
                pass
            frame = ttk.Frame(root, padding=18)
            frame.pack(fill="both", expand=True)
            ttk.Label(
                frame,
                text="CoD2 Chat Translator",
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w")
            self.status = tk.StringVar(value=localized(self.lang, "Подготовка обновления…", "Preparing update…", "Підготовка оновлення…"))
            self.detail = tk.StringVar(value="")
            ttk.Label(frame, textvariable=self.status, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 4))
            ttk.Label(frame, textvariable=self.detail, foreground="#666666").pack(anchor="w", pady=(0, 8))
            self.bar = ttk.Progressbar(frame, mode="indeterminate", length=390)
            self.bar.pack(fill="x")
            self.bar.start(12)
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            root.update_idletasks()
            w, h = 440, 155
            x = max(0, (root.winfo_screenwidth() - w) // 2)
            y = max(0, (root.winfo_screenheight() - h) // 2)
            root.geometry(f"{w}x{h}+{x}+{y}")
            root.update()
            self.root = root
        except Exception:
            self.root = None

    def set(self, ru: str, en: str, detail: str = "", uk: str | None = None) -> None:
        if not self.root:
            return
        try:
            if self.status is not None:
                self.status.set(localized(self.lang, ru, en, uk))
            if self.detail is not None:
                self.detail.set(detail)
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def finish(self, ru: str, en: str, uk: str | None = None) -> None:
        if not self.root:
            return
        try:
            if self.bar is not None:
                self.bar.stop()
                self.bar.configure(mode="determinate", maximum=100, value=100)
            self.set(ru, en, uk=uk)
            self.root.update()
        except Exception:
            pass

    def close(self) -> None:
        if not self.root:
            return
        try:
            self.root.destroy()
        except Exception:
            pass
        self.root = None


def show_error(text: str, lang: str, ui: ProgressUI | None = None) -> None:
    title = localized(lang, "Ошибка обновления", "Update error", "Помилка оновлення")
    if ui:
        ui.close()
    if tk and messagebox:
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror(title, text)
            root.destroy(); return
        except Exception:
            pass
    print(f"{title}: {text}", file=sys.stderr)


def wait_pid(pid: int, timeout: float = 30.0) -> None:
    if pid <= 0:
        return
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if os.name == "nt":
                import ctypes
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                SYNCHRONIZE = 0x00100000
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
                if not handle:
                    return
                WAIT_TIMEOUT = 0x102
                result = ctypes.windll.kernel32.WaitForSingleObject(handle, 250)
                ctypes.windll.kernel32.CloseHandle(handle)
                if result != WAIT_TIMEOUT:
                    return
            else:
                os.kill(pid, 0)
                time.sleep(0.25)
        except Exception:
            return


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "CoD2ChatTranslator-Updater"})
    with urllib.request.urlopen(req, timeout=30) as response, path.open("wb") as out:
        shutil.copyfileobj(response, out)


def unsafe_archive_members(names: list[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        # ZIP uses '/' internally, but normalize backslashes too for defensive checks.
        normalized = name.replace("\\", "/")
        p = Path(normalized)
        if p.is_absolute() or ".." in p.parts or (p.parts and ":" in p.parts[0]):
            bad.append(name)
    return bad


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pid", type=int, default=0)
    p.add_argument("--install-dir", required=True)
    p.add_argument("--download-url", required=True)
    p.add_argument("--sha256", required=True)
    p.add_argument("--main-exe", default="CoD2ChatTranslator.exe")
    p.add_argument("--version", default="")
    p.add_argument("--ui-language", default="ru")
    args = p.parse_args()

    lang = args.ui_language if args.ui_language in {"ru", "uk", "en"} else "ru"
    ui = ProgressUI(lang)
    install_dir = Path(args.install_dir).resolve()
    if not install_dir.exists():
        show_error(localized(lang, "Папка программы не найдена.", "Application directory was not found.", "Папку програми не знайдено."), lang, ui)
        return 2

    version_detail = f"v{args.version}" if args.version else ""
    with tempfile.TemporaryDirectory(prefix="cod2chat_update_") as tmp:
        tmpdir = Path(tmp)
        package = tmpdir / "update.zip"
        staging = tmpdir / "staging"
        backup = tmpdir / "backup"
        replaced: list[Path] = []
        created: list[Path] = []
        try:
            ui.set("Скачивание обновления…", "Downloading update…", version_detail, uk="Завантаження оновлення…")
            download(args.download_url, package)

            ui.set("Проверка обновления…", "Verifying update…", "SHA256", uk="Перевірка оновлення…")
            actual_sha = sha256_file(package).lower()
            expected_sha = args.sha256.lower().strip()
            if actual_sha != expected_sha:
                raise RuntimeError("SHA256 mismatch")

            ui.set("Подготовка файлов…", "Preparing files…", version_detail, uk="Підготовка файлів…")
            with zipfile.ZipFile(package) as zf:
                bad = unsafe_archive_members(zf.namelist())
                if bad:
                    raise RuntimeError("Unsafe update archive")
                zf.extractall(staging)

            # Wait until the old application has actually closed before replacing its EXE.
            ui.set("Закрытие старой версии…", "Closing previous version…", uk="Закриття попередньої версії…")
            wait_pid(args.pid)

            ui.set("Установка обновления…", "Installing update…", version_detail, uk="Встановлення оновлення…")
            backup.mkdir(parents=True, exist_ok=True)
            for src in staging.rglob("*"):
                if not src.is_file():
                    continue
                rel = src.relative_to(staging)
                dest = install_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    b = backup / rel
                    b.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, b)
                else:
                    created.append(rel)
                shutil.copy2(src, dest)
                replaced.append(rel)

            main_exe = install_dir / args.main_exe
            if not main_exe.exists():
                raise RuntimeError(f"Missing {args.main_exe} after update")

        except Exception as exc:
            # Best-effort rollback: restore replaced files and remove files created by the failed update.
            try:
                if backup.exists():
                    for src in backup.rglob("*"):
                        if src.is_file():
                            rel = src.relative_to(backup)
                            dest = install_dir / rel
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dest)
                for rel in reversed(created):
                    dest = install_dir / rel
                    if dest.exists() and dest.is_file() and not (backup / rel).exists():
                        try:
                            dest.unlink()
                        except Exception:
                            pass
            except Exception:
                pass
            show_error(localized(lang, f"Не удалось установить обновление: {exc}", f"Could not install update: {exc}", f"Не вдалося встановити оновлення: {exc}"), lang, ui)
            return 3

    main_exe = install_dir / args.main_exe
    ui.finish("Обновление установлено. Запускаю программу…", "Update installed. Starting the app…", uk="Оновлення встановлено. Запускаю програму…")
    try:
        kwargs = {
            "cwd": str(install_dir),
            "close_fds": True,
        }
        flags = no_window_creationflags()
        if flags:
            kwargs["creationflags"] = flags
        subprocess.Popen([str(main_exe)], **kwargs)
        time.sleep(0.7)
    except Exception as exc:
        show_error(localized(lang, f"Обновление установлено, но программу не удалось запустить: {exc}", f"Update installed, but the app could not be started: {exc}", f"Оновлення встановлено, але програму не вдалося запустити: {exc}"), lang, ui)
        return 4
    ui.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
