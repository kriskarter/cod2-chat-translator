"""Exercise the visible English Inno wizard on an isolated Windows runner."""
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

REQUIRED_CAPTURES = {"welcome", "installing", "finish"}


def children_of(process):
    """Snapshot descendants, allowing the parent to exit during enumeration.

    Popen owns the original process handle; use it to distinguish an ordinary
    exit from an unexpected psutil failure, even when Windows removes the PID.
    """
    if process.poll() is not None:
        return []
    try:
        return psutil.Process(process.pid).children(recursive=True)
    except psutil.NoSuchProcess:
        if process.poll() is None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                # The original process is still running: don't hide the error.
                raise psutil.NoSuchProcess(process.pid) from None
        return []


def verify_exit(process, seen):
    code = process.poll()
    if code != 0 or seen != REQUIRED_CAPTURES:
        raise RuntimeError(f"Wizard exit={code}, captured={sorted(seen)}")


def stop_process_tree(process):
    for child in children_of(process):
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            # A child can exit after enumeration.
            continue
    if process.poll() is None:
        try:
            process.terminate()
        except ProcessLookupError:
            if process.poll() is None:
                raise


def stop_launched_app(install_dir):
    # Only stop the EXE started by this test installation.
    target = os.path.normcase(str(install_dir / "CoD2ChatTranslatorQt.exe"))
    for child in psutil.process_iter(["exe"]):
        try:
            if os.path.normcase(child.info["exe"] or "") == target:
                child.terminate()
        except psutil.NoSuchProcess:
            continue


def main(setup, install_dir, evidence):
    # GUI-only imports keep the process lifecycle helpers unit-testable.
    from PIL import ImageGrab, ImageStat
    from pywinauto import Desktop

    desktop = Desktop(backend="win32")
    evidence.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen([str(setup.resolve()), "/LANG=english", "/SP-",
                                "/NORESTART", "/SUPPRESSMSGBOXES", f"/DIR={install_dir}"])
    deadline = time.monotonic() + 150
    seen, clicked = set(), {}

    def capture(window, name):
        shot = ImageGrab.grab(window=window.handle)
        if min(shot.size) < 200 or max(ImageStat.Stat(shot.convert("RGB")).stddev) < 3:
            raise RuntimeError(f"Blank wizard capture: {name}")
        shot.save(evidence / f"installer_{name}.png")
        seen.add(name)

    try:
        while process.poll() is None and time.monotonic() < deadline:
            children = children_of(process)
            # Re-check the original process after the potentially racing query.
            if process.poll() is not None:
                break
            family = {process.pid, *(child.pid for child in children)}
            windows = [w for w in desktop.windows(class_name="TWizardForm") if w.process_id() in family]
            if not windows:
                time.sleep(.1)
                continue
            window = windows[0]
            controls = [c for c in window.descendants() if c.is_visible()]
            if any("ProgressBar" in c.class_name() for c in controls) and "installing" not in seen:
                capture(window, "installing")
            buttons = {c.window_text().replace("&", "").strip().lower(): c for c in controls
                       if "Button" in c.class_name() and c.is_enabled()}
            for name in ("finish", "install", "next"):
                if name not in buttons or time.monotonic() - clicked.get(name, 0) < .7:
                    continue
                if name == "next" and not seen:
                    capture(window, "welcome")
                if name == "finish":
                    if "finish" not in seen:
                        capture(window, "finish")
                        # The list contains the single launch-after-install action.
                        for c in controls:
                            if c.class_name() == "TNewCheckListBox":
                                c.set_focus()
                                c.type_keys("{SPACE}")
                ctypes.windll.user32.PostMessageW(buttons[name].handle, 0x00F5, 0, 0)
                clicked[name] = time.monotonic()
                break
            time.sleep(.08)
        verify_exit(process, seen)
        for name in REQUIRED_CAPTURES:
            shot = evidence / f"installer_{name}.png"
            if not shot.is_file() or shot.stat().st_size == 0:
                raise RuntimeError(f"Missing wizard screenshot: {name}")
    finally:
        try:
            stop_process_tree(process)
        finally:
            stop_launched_app(install_dir)


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
