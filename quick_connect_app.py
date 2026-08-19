from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path
from typing import Iterable, Optional

import app as core


SERVER_NAME = "CLASSIC OBORONA"
SERVER_SUBTITLE = "CoD2 1.3 · 24/7"
SERVER_ADDRESS = "146.59.34.100:28960"
SERVER_DISCORD_URL = "https://discord.gg/qxwBpzJ"
SERVER_LOGO_B64 = """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"""


def _path_key(path: Path | str) -> str:
    return os.path.normcase(str(Path(path).expanduser().resolve(strict=False)))


def unique_roots(roots: Iterable[Path | str]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for raw in roots:
        try:
            path = Path(raw).expanduser().resolve(strict=False)
        except Exception:
            continue
        key = _path_key(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def find_multiplayer_executable(roots: Iterable[Path | str]) -> Optional[Path]:
    names = ("CoD2MP_s.exe", "CoD2MP.exe", "cod2mp_s.exe", "cod2mp.exe", "cod2_mp.exe")
    for root in unique_roots(roots):
        for name in names:
            candidate = root / name
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                pass
    return None


def build_connect_command(executable: Path | str, address: str = SERVER_ADDRESS) -> list[str]:
    return [str(Path(executable)), "+connect", address]


def no_window_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0))


def launch_connect_command(executable: Path | str, address: str = SERVER_ADDRESS) -> None:
    executable = Path(executable).expanduser().resolve(strict=False)

    kwargs = {"cwd": str(executable.parent), "close_fds": True}
    flags = no_window_creationflags()
    if flags:
        kwargs["creationflags"] = flags

    try:
        subprocess.Popen(build_connect_command(executable, address), **kwargs)
        return
    except OSError as exc:
        # WinError 740: this CoD2 executable is configured to require elevation.
        # Ask Windows for elevation instead of requiring the translator itself
        # to always run as administrator.
        if os.name != "nt" or getattr(exc, "winerror", None) != 740:
            raise

    parameters = subprocess.list2cmdline(["+connect", address])
    result = int(
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            str(executable),
            parameters,
            str(executable.parent),
            1,
        )
    )
    if result <= 32:
        raise OSError(f"ShellExecuteW failed with code {result}")


def _localized(app: core.ControlApp, ru: str, en: str) -> str:
    return en if getattr(app, "ui_language", "ru") == "en" else ru


def _candidate_game_roots(app: core.ControlApp) -> list[Path]:
    roots: list[Path | str] = []
    try:
        preferred = app._preferred_game_root()
        if preferred is not None:
            roots.append(preferred)
    except Exception:
        pass

    roots.extend(app.config.get("cod2_roots", []) or [])

    try:
        roots.extend(core.discover_running_cod2_roots())
    except Exception:
        pass

    try:
        roots.extend(core.discover_cod2_game_roots(app.config.get("cod2_roots", []) or []))
    except Exception:
        pass

    return unique_roots(roots)


def _launch_featured_server(app: core.ControlApp) -> None:
    if os.name != "nt":
        app.status_var.set(_localized(app, "Быстрый вход доступен только в Windows.", "Quick connect is available on Windows only."))
        return

    executable = find_multiplayer_executable(_candidate_game_roots(app))
    if executable is None:
        core.messagebox.showwarning(
            core.APP_NAME,
            _localized(
                app,
                "Не удалось найти CoD2 Multiplayer. Запусти игру один раз или укажи папку игры в «Настройки сервера…».",
                "CoD2 Multiplayer was not found. Start the game once or choose its folder in Server settings.",
            ),
            parent=app.root,
        )
        return

    try:
        try:
            app._remember_cod2_root(executable.parent)
            app._persist_settings()
        except Exception:
            pass

        launch_connect_command(executable)
        app.status_var.set(
            _localized(
                app,
                f"Запускаю {SERVER_NAME} · {SERVER_ADDRESS}",
                f"Starting {SERVER_NAME} · {SERVER_ADDRESS}",
            )
        )
    except Exception as exc:
        core.messagebox.showerror(
            core.APP_NAME,
            _localized(app, f"Не удалось запустить CoD2: {exc}", f"Could not start CoD2: {exc}"),
            parent=app.root,
        )


def _open_discord(app: core.ControlApp) -> None:
    try:
        webbrowser.open(SERVER_DISCORD_URL, new=2)
        app.status_var.set(_localized(app, "Открываю Discord сервера CLASSIC OBORONA.", "Opening the CLASSIC OBORONA Discord."))
    except Exception as exc:
        core.messagebox.showerror(core.APP_NAME, str(exc), parent=app.root)


def _inject_quick_connect_card(app: core.ControlApp) -> None:
    lang_frame = getattr(getattr(app, "language_combo", None), "master", None)
    if lang_frame is None:
        return
    outer = getattr(lang_frame, "master", None)
    if outer is None:
        return

    card = core.ttk.LabelFrame(
        outer,
        text=_localized(app, "Быстрый вход", "Quick connect"),
        padding=(12, 8),
    )
    card.pack(fill="x", pady=(10, 0), before=lang_frame)

    logo_box = core.ttk.Frame(card, width=180, height=86)
    logo_box.pack(side="left", padx=(0, 14))
    logo_box.pack_propagate(False)
    try:
        logo = core.tk.PhotoImage(data=SERVER_LOGO_B64, format="png")
        app._oborona_server_logo = logo
        core.ttk.Label(logo_box, image=logo).pack(expand=True)
    except Exception:
        core.ttk.Label(logo_box, text=SERVER_NAME, font=("Segoe UI", 11, "bold")).pack(expand=True)

    info = core.ttk.Frame(card)
    info.pack(side="left", fill="both", expand=True)
    core.ttk.Label(info, text=SERVER_NAME, font=("Segoe UI", 12, "bold")).pack(anchor="w")
    core.ttk.Label(info, text=SERVER_SUBTITLE, foreground="#666666").pack(anchor="w", pady=(3, 0))
    core.ttk.Label(info, text=SERVER_ADDRESS, font=("Consolas", 10, "bold")).pack(anchor="w", pady=(8, 0))

    actions = core.ttk.Frame(card)
    actions.pack(side="right", padx=(16, 0))
    core.ttk.Button(
        actions,
        text=_localized(app, "▶  Подключиться", "▶  Connect"),
        command=lambda: _launch_featured_server(app),
        width=20,
    ).pack(fill="x")
    core.ttk.Button(
        actions,
        text="Discord",
        command=lambda: _open_discord(app),
        width=20,
    ).pack(fill="x", pady=(7, 0))


def _launch_updater_quiet(app: core.ControlApp, info: core.UpdateInfo) -> None:
    install_dir = core.app_dir()
    updater_name = "CoD2ChatTranslatorUpdater.exe"
    main_name = Path(sys.executable).name if getattr(sys, "frozen", False) else "CoD2ChatTranslator.exe"
    try:
        if getattr(sys, "frozen", False):
            source_updater = install_dir / updater_name
            if not source_updater.exists():
                raise FileNotFoundError(updater_name)
            temp_updater = Path(tempfile.gettempdir()) / f"CoD2ChatTranslatorUpdater_{int(time.time())}.exe"
            shutil.copy2(source_updater, temp_updater)
            cmd = [str(temp_updater)]
        else:
            source = core.app_dir() / "updater.py"
            cmd = [sys.executable, str(source)]

        cmd += [
            "--pid", str(os.getpid()),
            "--install-dir", str(install_dir),
            "--download-url", info.download_url,
            "--sha256", info.sha256,
            "--main-exe", main_name,
            "--version", info.version,
            "--ui-language", app.ui_language,
        ]

        kwargs = {"cwd": str(install_dir), "close_fds": True}
        flags = no_window_creationflags()
        if flags:
            kwargs["creationflags"] = flags
        subprocess.Popen(cmd, **kwargs)
        app.close()
    except Exception as exc:
        core.messagebox.showerror(core.APP_NAME, app.t("update_error").format(error=exc), parent=app.root)


def install_feature() -> None:
    if getattr(core.ControlApp, "_quick_connect_oborona_installed", False):
        return

    original_build_ui = core.ControlApp._build_ui

    def build_ui_with_quick_connect(self: core.ControlApp) -> None:
        original_build_ui(self)
        _inject_quick_connect_card(self)

    core.ControlApp._build_ui = build_ui_with_quick_connect
    core.ControlApp._launch_updater = _launch_updater_quiet
    core.ControlApp._quick_connect_oborona_installed = True


def main() -> int:
    install_feature()

    if core.tk is None:
        print("Tkinter is not available in this Python installation.", file=sys.stderr)
        return 2

    root = core.tk.Tk()
    try:
        core.ControlApp(root)
        root.title(f"{core.APP_NAME} v{core.APP_VERSION} — Quick Connect TEST")
        root.mainloop()
        return 0
    except Exception as exc:
        try:
            core.messagebox.showerror(core.APP_NAME, str(exc))
        except Exception:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
