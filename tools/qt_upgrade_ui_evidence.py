"""Native Windows installed-EXE UI regression; never seed the test server in JSON."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab
from pywinauto import Desktop

OLD, NEW, INSTALL, PROFILE, EVIDENCE = map(lambda x: Path(x).resolve(), sys.argv[1:])
PROFILE.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
SETTINGS = PROFILE / "qt_settings.json"
SOURCE = PROFILE / "legacy_config.json"
assert not SETTINGS.exists(), "Native acceptance requires a fresh isolated profile"
# Only control the language and profile discovery; leave the stock server list
# untouched. Every test server/friend must be entered through visible controls.
SOURCE.write_text(json.dumps({"ui_language":"en","auto_detect_profile":False,
                              "qt_hint_dismissed":True}), encoding="utf-8")
SERVER = "148.251.139.73:12345"
LABEL = "Massacre Extreme All Weapons TDM"
FRIEND = "AcceptanceMedic"
DESKTOP = Desktop(backend="win32")
UIA = Desktop(backend="uia")


def wait_for(predicate, label, timeout=20):
    until = time.monotonic() + timeout
    last = None
    while time.monotonic() < until:
        try:
            result = predicate()
            if result:
                return result
        except Exception as error:
            last = error
        time.sleep(.15)
    raise AssertionError(f"Timeout: {label}; last={last!r}")


def install(setup):
    subprocess.run([str(setup),"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART",
                    "/LANG=english",f"/DIR={INSTALL}"], check=True, timeout=180)


def launch():
    process = subprocess.Popen([str(INSTALL/"CoD2ChatTranslatorQt.exe"),
        "--config",str(SOURCE),"--settings-file",str(SETTINGS),
        "--knowledge-file",str(PROFILE/"knowledge.json"),"--size","1342x672",
        "--ui-language","en"], env=dict(os.environ,QT_QPA_PLATFORM="windows",
        QT_SCALE_FACTOR="1",QT_ACCESSIBILITY="1"))
    try:
        native = wait_for(lambda: next((w for w in DESKTOP.windows(process=process.pid)
            if w.is_visible() and "CoD2 Chat Translator" in w.window_text()),None),
            "native application window",45)
        native.set_focus()
        window = UIA.window(handle=native.handle).wrapper_object()
        wait_for(lambda: controls(window,"Button","Add server"),"QML UIA home buttons")
        return process,native,window
    except BaseException:
        process.terminate()
        process.wait(timeout=10)
        raise


def controls(window, role, name=None):
    return [w for w in window.descendants(control_type=role)
            if w.is_visible() and w.is_enabled()
            and (name is None or w.window_text().strip()==name)]


def press(control):
    try:
        control.invoke()
    except Exception:
        control.click_input()
    time.sleep(.3)


def button(window, text):
    return wait_for(lambda: next(iter(controls(window,"Button",text)),None),text)


def fill(control, value):
    # UIA writes the actual QML TextField, not configuration data.
    try:
        control.set_edit_text(value)
    except Exception:
        control.click_input()
        control.type_keys("^a{BACKSPACE}")
        control.type_keys(value, with_spaces=True, pause=.015)
    time.sleep(.15)


def save_capture(native, name):
    shot = ImageGrab.grab(window=native.handle)
    assert shot.width > 800 and shot.height > 450
    shot.save(EVIDENCE/f"upgrade_ui_{name}.png")


def read_config():
    return json.loads(SETTINGS.read_text(encoding="utf-8-sig"))


def record(config, address):
    return next((s for s in config.get("server_monitor",{}).get("servers",[])
                 if s.get("address")==address),None)


def close(process, native):
    native.close()
    process.wait(timeout=25)
    assert process.returncode==0


def cleanup(process):
    if process.poll() is None:
        process.terminate()
        process.wait(timeout=10)


def add_server(window, address, port, label):
    press(button(window,"Add server"))
    def dialog_edits():
        edits=sorted(controls(window,"Edit"),key=lambda w:w.rectangle().top)
        return edits if len(edits)==3 else None
    host, port_field, name = wait_for(dialog_edits,"three add-server form fields")
    fill(host,address)
    fill(port_field,port)
    fill(name,label)
    press(button(window,"Add"))
    wait_for(lambda: not controls(window,"Edit"),"server form closes")


def verify_visible(window, label):
    # The server table may expose the label as text or a row's accessible name.
    return wait_for(lambda: any(label in w.window_text() for w in window.descendants()
                                if w.is_visible()), f"visible server {label}")


def add_friend(window):
    press(button(window,"Servers"))
    def fields():
        edits=sorted(controls(window,"Edit"),key=lambda w:w.rectangle().top)
        return edits if len(edits)>=4 else None
    friend = wait_for(fields,"server workspace nickname field")[-1]
    fill(friend,FRIEND)
    def closest_add():
        choices=controls(window,"Button","Add")
        if not choices:
            return None
        return min(choices,key=lambda w:abs(w.rectangle().mid_point().y-friend.rectangle().mid_point().y)
                   +abs(w.rectangle().mid_point().x-friend.rectangle().mid_point().x)/4)
    press(wait_for(closest_add,"add friend button"))


def assert_legacy_data():
    cfg=read_config()
    assert record(cfg,SERVER) is not None and record(cfg,SERVER)["label"]==LABEL
    assert FRIEND in cfg["server_monitor"]["friends"]
    assert cfg["qt_f8_enabled"] is False and cfg["outgoing_enabled"] is False
    return cfg


install(OLD)
process,native,window=launch()
try:
    add_server(window,"148.251.139.73","12345",LABEL)
    verify_visible(window,LABEL)
    press(button(window,"F8"))
    press(button(window,"F9"))
    add_friend(window)
    # The legacy release's no-op _settings_changed requires this explicit
    # action. The new release must not require it.
    press(button(window,"Save settings"))
    wait_for(lambda: SETTINGS.exists() and record(read_config(),SERVER),"legacy explicit save")
    assert_legacy_data()
    save_capture(native,"old_saved")
    close(process,native)
finally:
    cleanup(process)

process,native,window=launch()
try:
    verify_visible(window,LABEL)
    assert_legacy_data()
    save_capture(native,"old_reopened")
    close(process,native)
finally:
    cleanup(process)

before=SETTINGS.read_bytes()
install(NEW)
assert SETTINGS.read_bytes()==before,"Installer changed legacy user configuration"
process,native,window=launch()
try:
    verify_visible(window,LABEL)
    assert_legacy_data()
    save_capture(native,"new_upgraded")
    add_server(window,"127.0.0.1","12346","Autosave acceptance")
    wait_for(lambda: record(read_config(),"127.0.0.1:12346"),"new autosave without Save settings")
    verify_visible(window,"Autosave acceptance")
    save_capture(native,"new_autosave")
    close(process,native)
finally:
    cleanup(process)

process,native,window=launch()
try:
    verify_visible(window,LABEL)
    verify_visible(window,"Autosave acceptance")
    assert_legacy_data()
    assert record(read_config(),"127.0.0.1:12346")
    save_capture(native,"new_reopened")
    close(process,native)
finally:
    cleanup(process)

before=SETTINGS.read_bytes()
install(NEW)
assert SETTINGS.read_bytes()==before
process,native,window=launch()
try:
    verify_visible(window,LABEL)
    verify_visible(window,"Autosave acceptance")
    assert_legacy_data()
    save_capture(native,"new_reinstalled")
    close(process,native)
finally:
    cleanup(process)

(EVIDENCE/"native_ui_upgrade.json").write_text(json.dumps({
    "old_release":"c9ec1acd8ca2","legacy_required_explicit_save":True,
    "server_entered_through_ui":SERVER,"friend_entered_through_ui":FRIEND,
    "reopen_upgrade_reinstall":True,"new_autosave_without_save_button":True,
    "native_uac_gameplay":"not exercised"
},indent=2),encoding="utf-8")
