"""Native Windows installed-EXE UI regression; never seed the test server in JSON."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab
from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys

OLD, NEW, INSTALL, PROFILE, EVIDENCE = map(lambda x: Path(x).resolve(), sys.argv[1:])
PROFILE.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
SETTINGS = PROFILE / "qt_settings.json"
SOURCE = PROFILE / "legacy_config.json"
assert not SETTINGS.exists(), "Native acceptance requires a fresh isolated profile"
# Only control the language and profile discovery; leave the stock server list
# untouched. Every test server/friend must be entered through visible controls.
SOURCE.write_text(json.dumps({"ui_language":"en","auto_detect_profile":False,
                              "qt_f8_enabled":True,"outgoing_enabled":True,
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
    # Physical click also works for QML controls with incomplete UIA patterns.
    control.click_input()
    time.sleep(.3)


def by_id(window, suffix, role=None, enabled=True):
    return next((w for w in window.descendants()
        if w.element_info.automation_id.endswith("."+suffix)
        and (role is None or w.element_info.control_type==role)
        and w.is_visible() and (not enabled or w.is_enabled())),None)

def button(window, text):
    return wait_for(lambda: next(iter(controls(window,"Button",text)),None),text)


def edit_value(control):
    return str(control.iface_value.CurrentValue)


def fill(control, value):
    # Real input exercises editingFinished and TextField bindings.
    control.click_input()
    send_keys("^a{BACKSPACE}")
    send_keys(value, with_spaces=True, pause=.015)
    wait_for(lambda: edit_value(control)==value, f"TextField exact value {value!r}")


def dump_uia(window, name):
    rows=[]
    for item in window.descendants():
        try:
            r=item.rectangle()
            info=item.element_info
            entry=dict(role=info.control_type,name=item.window_text(),
                automation_id=info.automation_id,visible=item.is_visible(),
                enabled=item.is_enabled(),rect=[r.left,r.top,r.right,r.bottom])
            if info.control_type=="Edit":
                entry["value"]=edit_value(item)
            rows.append(entry)
        except Exception as error:
            rows.append({"error":repr(error)})
    (EVIDENCE/f"uia_{name}.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    return rows


def exact_text(window, value):
    return next((w for w in window.descendants()
                 if w.is_visible() and w.window_text().strip()==value),None)


def check_record(address,label):
    def matches():
        if not SETTINGS.exists():
            return False
        row=record(read_config(),address)
        return row is not None and row.get("label")==label
    return wait_for(matches,f"persisted exact server {address} / {label}")


def open_servers(window):
    press(button(window,"Servers"))
    wait_for(lambda: controls(window,"Button","Save settings"),"server workspace loaded")


def home(window):
    press(button(window,"Home"))
    wait_for(lambda: controls(window,"Button","Add server"),"home loaded")


def editor_fields(window):
    return [by_id(window,key,"Edit",enabled=False) for key in
            ("editServerHost","editServerPort","serverLabelInput")]


def editor_values(window):
    edits=editor_fields(window)
    return tuple(edit_value(w) for w in edits) if all(edits) else ()

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


def add_server(window,address,port,label):
    press(button(window,"Add server"))
    fields=[]
    for key in ("serverHostInput","serverPortInput","serverNameInput"):
        fields.append(wait_for(lambda: by_id(window,key,"Edit"),key))
    for field,value in zip(fields,(address,port,label)):
        fill(field,value)
    assert tuple(map(edit_value,fields))==(address,port,label)
    # c9ec1acd8ca2 does not expose any static QML Text to Windows UIA,
    # including its address preview. Exact fields + enabled validated Add +
    # closed dialog + exact selected editor + persistent record prove the add.
    dump_uia(window,"form_"+port)
    press(button(window,"Add"))
    wait_for(lambda: by_id(window,"serverHostInput","Edit") is None,
             "server form closes after accepted add")

def verify_visible(window,address,label,stage):
    # Legacy static Text and the ListView rows are absent from the UIA tree.
    # New RC exposes ListItem name/address explicitly. For both versions,
    # select an actual row and check the complete editable values.
    open_servers(window)
    host,port=address.rsplit(":",1)
    expected=(host,port,label)
    before=dump_uia(window,stage+"_before_scroll")
    print(f"{stage}: full name exposed in UIA: "
          f"{any(label in row.get('name','') and row.get('role')!='Edit' for row in before)}",
          flush=True)
    anchor=wait_for(lambda: by_id(window,"editServerHost","Edit",enabled=False),
                    "server editor host")
    r=anchor.rectangle()
    nav=wait_for(lambda: by_id(window,"nav_home","Button"),"navigation anchor").rectangle()
    x=(nav.left+r.left)//2
    # Same workspace geometry in old and new RC: left table header aligns
    # with the right host field, row height 32 and viewport at most 86.
    # Derive coordinates from actual native UIA rectangles, not screen origin.
    y=r.top
    for step in range(35):
        if editor_values(window)==expected:
            break
        row=next((w for w in window.descendants()
                  if w.is_visible() and w.element_info.control_type=="ListItem"
                  and label in w.window_text() and address in w.window_text()),None)
        if row is not None:
            row.click_input()
            time.sleep(.2)
        if editor_values(window)==expected:
            break
        for dy in (23,35,49,61,73,83):
            mouse.click(coords=(x,y+dy))
            time.sleep(.15)
            if editor_values(window)==expected:
                break
        if editor_values(window)==expected:
            break
        mouse.scroll(coords=(x,y+35),wheel_dist=-1)
        time.sleep(.2)
    else:
        dump_uia(window,stage+"_not_found")
        raise AssertionError(f"{stage}: no selectable server with exact editor values "
                             f"{expected!r}; last={editor_values(window)!r}")
    assert editor_values(window)==expected
    dump_uia(window,stage+"_selected")
    print(f"{stage}: exact UI editor values {expected!r}",flush=True)
    check_record(address,label)
    home(window)

def add_friend(window):
    indicator=wait_for(lambda: by_id(window,"friends_indicator","Button"),
                       "friends indicator")
    press(indicator)
    friend=wait_for(lambda: next(iter(controls(window,"Edit")),None),"friends popup nickname")
    fill(friend,FRIEND)
    fr=friend.rectangle()
    def popup_add():
        return next((w for w in controls(window,"Button","Add friend")
                     if abs(w.rectangle().mid_point().y-fr.mid_point().y)<25
                     and w.rectangle().left>=fr.right-5),None)
    press(wait_for(popup_add,"friends popup add button"))
    wait_for(lambda: SETTINGS.exists() and FRIEND in
             read_config().get("server_monitor",{}).get("friends",[]),"friend autosave")
    def popup_close():
        return next((w for w in controls(window,"Button","Close")
                     if w.element_info.automation_id and
                     0<fr.top-w.rectangle().top<160),None)
    press(wait_for(popup_close,"friends popup close"))
    wait_for(lambda: not controls(window,"Edit"),"friends popup closes")

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
    # Old RC requires explicit save. Separate real addition from UI visibility.
    press(button(window,"F8"))
    press(button(window,"F9"))
    open_servers(window)
    press(button(window,"Save settings"))
    check_record(SERVER,LABEL)
    home(window)
    verify_visible(window,SERVER,LABEL,"old_saved")
    add_friend(window)
    assert_legacy_data()
    save_capture(native,"old_saved")
    close(process,native)
except BaseException:
    try:
        dump_uia(window,"failure")
        save_capture(native,"failure")
    except Exception as error:
        print(f"Failure evidence unavailable: {error!r}",flush=True)
    raise
finally:
    cleanup(process)

process,native,window=launch()
try:
    verify_visible(window,SERVER,LABEL,"old_reopened")
    assert_legacy_data()
    save_capture(native,"old_reopened")
    close(process,native)
except BaseException:
    try:
        dump_uia(window,"failure")
        save_capture(native,"failure")
    except Exception as error:
        print(f"Failure evidence unavailable: {error!r}",flush=True)
    raise
finally:
    cleanup(process)

before=SETTINGS.read_bytes()
install(NEW)
assert SETTINGS.read_bytes()==before,"Installer changed legacy user configuration"
process,native,window=launch()
try:
    verify_visible(window,SERVER,LABEL,"new_upgraded")
    assert_legacy_data()
    save_capture(native,"new_upgraded")
    add_server(window,"127.0.0.1","12346","Autosave acceptance")
    check_record("127.0.0.1:12346","Autosave acceptance")
    verify_visible(window,"127.0.0.1:12346","Autosave acceptance","new_autosave_second")
    save_capture(native,"new_autosave")
    close(process,native)
except BaseException:
    try:
        dump_uia(window,"failure")
        save_capture(native,"failure")
    except Exception as error:
        print(f"Failure evidence unavailable: {error!r}",flush=True)
    raise
finally:
    cleanup(process)

process,native,window=launch()
try:
    verify_visible(window,SERVER,LABEL,"new_reopened")
    verify_visible(window,"127.0.0.1:12346","Autosave acceptance","new_reopened_second")
    assert_legacy_data()
    check_record("127.0.0.1:12346","Autosave acceptance")
    save_capture(native,"new_reopened")
    close(process,native)
except BaseException:
    try:
        dump_uia(window,"failure")
        save_capture(native,"failure")
    except Exception as error:
        print(f"Failure evidence unavailable: {error!r}",flush=True)
    raise
finally:
    cleanup(process)

before=SETTINGS.read_bytes()
install(NEW)
assert SETTINGS.read_bytes()==before
process,native,window=launch()
try:
    verify_visible(window,SERVER,LABEL,"new_reinstalled")
    verify_visible(window,"127.0.0.1:12346","Autosave acceptance","new_reinstalled_second")
    assert_legacy_data()
    save_capture(native,"new_reinstalled")
    close(process,native)
except BaseException:
    try:
        dump_uia(window,"failure")
        save_capture(native,"failure")
    except Exception as error:
        print(f"Failure evidence unavailable: {error!r}",flush=True)
    raise
finally:
    cleanup(process)

(EVIDENCE/"native_ui_upgrade.json").write_text(json.dumps({
    "old_release":"c9ec1acd8ca2","legacy_required_explicit_save":True,
    "server_entered_through_ui":SERVER,"friend_entered_through_ui":FRIEND,
    "reopen_upgrade_reinstall":True,"new_autosave_without_save_button":True,
    "native_uac_gameplay":"not exercised"
},indent=2),encoding="utf-8")
