"""Exercise the visible English Inno wizard on an isolated Windows runner."""
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
from PIL import ImageGrab, ImageStat
from pywinauto import Desktop

setup, install_dir, evidence = map(Path, sys.argv[1:])
process = subprocess.Popen([str(setup.resolve()), "/LANG=english", "/SP-", "/NORESTART",
                            "/SUPPRESSMSGBOXES", f"/DIR={install_dir}"])
desktop = Desktop(backend="win32")
deadline = time.monotonic() + 150
seen, clicked = set(), {}
evidence.mkdir(parents=True, exist_ok=True)

def capture(window, name):
    shot = ImageGrab.grab(window=window.handle)
    if min(shot.size) < 200 or max(ImageStat.Stat(shot.convert("RGB")).stddev) < 3:
        raise RuntimeError(f"Blank wizard capture: {name}")
    shot.save(evidence / f"installer_{name}.png")
    seen.add(name)

try:
    while process.poll() is None and time.monotonic() < deadline:
        family = {process.pid, *(child.pid for child in psutil.Process(process.pid).children(recursive=True))}
        windows = [w for w in desktop.windows(class_name="TWizardForm") if w.process_id() in family]
        if not windows:
            time.sleep(.1)
            continue
        window = windows[0]
        children = [c for c in window.descendants() if c.is_visible()]
        if any("ProgressBar" in c.class_name() for c in children) and "installing" not in seen:
            capture(window,"installing")
        buttons = {c.window_text().replace("&","").strip().lower():c for c in children
                   if "Button" in c.class_name() and c.is_enabled()}
        for name in ("finish","install","next"):
            if name not in buttons or time.monotonic() - clicked.get(name,0) < .7:
                continue
            if name == "next" and not seen:
                capture(window,"welcome")
            if name == "finish":
                if "finish" not in seen:
                    capture(window,"finish")
                    # The list contains the single launch-after-install action.
                    for c in children:
                        if c.class_name()=="TNewCheckListBox":
                            c.set_focus()
                            c.type_keys("{SPACE}")
            ctypes.windll.user32.PostMessageW(buttons[name].handle, 0x00F5, 0, 0)
            clicked[name] = time.monotonic()
            break
        time.sleep(.08)
    if process.poll() != 0 or seen != {"welcome","installing","finish"}:
        raise RuntimeError(f"Wizard exit={process.poll()}, captured={sorted(seen)}")
finally:
    if process.poll() is None:
        for child in psutil.Process(process.pid).children(recursive=True):
            child.terminate()
        process.terminate()
    # Only stop the EXE started by this test installation.
    for child in psutil.process_iter(["exe"]):
        if os.path.normcase(child.info["exe"] or "") == os.path.normcase(str(install_dir/"CoD2ChatTranslatorQt.exe")):
            child.terminate()
