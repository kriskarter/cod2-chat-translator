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

OLD, NEW, INSTALL, PROFILE, EVIDENCE = map(lambda x: Path(x).resolve(), sys.argv[1:6])
CANDIDATE = os.environ.get("COD2_STABLE_CANDIDATE") == "1"
PREVIOUS = Path(sys.argv[6]).resolve() if len(sys.argv)>6 else None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qt_experiment.shortcut_diagnostics import elevated
import ctypes
import psutil
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


def automation_id(control):
    # UIA providers may expose no AutomationId (None, not just "").
    return control.element_info.automation_id or ""


def by_id(window,suffix,role=None,enabled=True):
    candidates=window.descendants(control_type=role) if role else window.descendants()
    for w in candidates:
        try:
            if (automation_id(w).endswith("."+suffix) and w.is_visible()
                    and (not enabled or w.is_enabled())):
                return w
        except Exception:
            # A volatile roster delegate can disappear during enumeration.
            continue
    return None

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


def editor_values(window):
    keys=("editServerHost","editServerPort","serverLabelInput")
    values={}
    for w in window.descendants(control_type="Edit"):
        try:
            key=automation_id(w).rsplit(".",1)[-1]
            if key in keys and w.is_visible():
                values[key]=edit_value(w)
        except Exception:
            continue
    return tuple(values[k] for k in keys) if all(k in values for k in keys) else ()

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
    legacy=stage.startswith("old_")
    check_record(address,label)
    open_servers(window)
    host,port=address.rsplit(":",1)
    expected=(host,port,label)
    before=dump_uia(window,stage+"_before_scroll")
    print(f"{stage}: full name exposed in UIA: "
          f"{any(label in row.get('name','') and row.get('role')!='Edit' for row in before)}",
          flush=True)
    anchor=wait_for(lambda: by_id(window,"editServerHost","Edit",enabled=False),
                    "server editor host")
    indicator=wait_for(lambda: by_id(window,"friends_indicator","Button"),
                       "server workspace friends indicator")
    r=anchor.rectangle()
    nav=wait_for(lambda: by_id(window,"nav_home","Button"),"navigation anchor").rectangle()
    x=(nav.left+r.left)//2
    y0=indicator.rectangle().bottom+48

    def selected_address():
        return editor_values(window)[:2]==expected[:2]

    # Select a genuine row, not a value typed into the editor. The legacy
    # table does not expose static QML text through Windows UIA.
    for step in range(30):
        if selected_address():
            break
        for w in window.descendants(control_type="ListItem"):
            try:
                if (w.is_visible() and label in w.window_text() and address in w.window_text()
                        and y0-10<=w.rectangle().mid_point().y<=y0+90):
                    w.click_input()
                    time.sleep(.2)
                    break
            except Exception:
                continue
        if selected_address():
            break
        for dy in (9,25,41,57,73):
            mouse.click(coords=(x,y0+dy))
            time.sleep(.15)
            if selected_address():
                break
        if selected_address():
            break
        mouse.scroll(coords=(x,y0+15),wheel_dist=-1)
        time.sleep(.2)
    else:
        dump_uia(window,stage+"_not_found")
        raise AssertionError(f"{stage}: no selectable server {address}; last={editor_values(window)!r}")

    actual=editor_values(window)
    if legacy and actual!=expected:
        # Observed in native run 46043202719: host/port switch immediately
        # but label/favorite still belong to the previous selection because
        # onSelectedAddressChanged reads a stale record binding. Recreating
        # the legacy editor (without changing anything) loads its real record.
        print(f"{stage}: legacy stale editor {actual!r}; reopen page",flush=True)
        dump_uia(window,stage+"_legacy_stale_editor")
        home(window)
        open_servers(window)
    # Never apply that workaround to the new RC: its live editor must
    # immediately agree with the selected address and exact full label.
    wait_for(lambda: editor_values(window)==expected,
             f"{stage}: exact selected editor values {expected!r}",timeout=10)
    dump_uia(window,stage+"_selected")
    save_capture(DESKTOP.window(handle=window.handle).wrapper_object(),stage+"_editor")
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
                     if automation_id(w) and
                     0<fr.top-w.rectangle().top<160),None)
    press(wait_for(popup_close,"friends popup close"))
    wait_for(lambda: not controls(window,"Edit"),"friends popup closes")

def assert_policy(process, expected=True):
    cfg=read_config()
    assert cfg["qt_admin_policy_version"]==1
    assert cfg["qt_always_admin"] is expected
    token=elevated(process.pid)
    assert token=="True", f"Expected elevated installed EXE token on CI runner, got {token!r}"
    return {"process_token_elevated":True,"startup_preference":expected,
            "policy_version":cfg["qt_admin_policy_version"]}


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
    print("legacy add and exact persisted label confirmed",flush=True)
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

# Retain original c9ec UI migration, and additionally exercise the exact
# previous accepted release before updating to the candidate.
if PREVIOUS is not None:
    before=SETTINGS.read_bytes()
    install(PREVIOUS)
    assert SETTINGS.read_bytes()==before,"Previous installer changed legacy settings"
    process,native,window=launch()
    try:
        verify_visible(window,SERVER,LABEL,"previous_9924")
        assert_legacy_data()
        save_capture(native,"previous_9924")
        close(process,native)
        old_cfg=read_config()
        assert old_cfg.get("qt_always_admin") is False
        assert "qt_admin_policy_version" not in old_cfg
    finally:
        cleanup(process)

before=SETTINGS.read_bytes()
install(NEW)
assert SETTINGS.read_bytes()==before,"Installer changed legacy user configuration"
process,native,window=launch()
try:
    verify_visible(window,SERVER,LABEL,"new_upgraded")
    assert_legacy_data()
    upgraded_policy=assert_policy(process)
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
    assert_policy(process)
    # The user's explicit opt-out in the new version must survive reopening.
    press(button(window,"Settings"))
    control=wait_for(lambda: by_id(window,"startupAdminSwitch","CheckBox"),
                     "startup administrator setting")
    assert control.get_toggle_state()==1
    press(control)
    wait_for(lambda: read_config().get("qt_always_admin") is False,
             "persist explicit startup opt-out")
    assert_policy(process,False)
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
    assert_policy(process,False)
    verify_visible(window,SERVER,LABEL,"opt_out_reopened")
    verify_visible(window,"127.0.0.1:12346","Autosave acceptance","opt_out_reopened_second")
    assert_legacy_data()
    save_capture(native,"opt_out_reopened")
    close(process,native)
finally:
    cleanup(process)

# A separate fresh Qt preference profile verifies clean first launch.
# The runner starts with its existing admin token; no interactive UAC
# consent or physical CoD2 game input is asserted here.
PROFILE=PROFILE/"clean"
PROFILE.mkdir()
SETTINGS=PROFILE/"qt_settings.json"
assert not SETTINGS.exists()
process,native,window=launch()
try:
    clean_policy=assert_policy(process)
    save_capture(native,"clean_policy")
    close(process,native)
finally:
    cleanup(process)

def shell_folder(csidl):
    buf=ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None,csidl,None,0,buf)!=0:
        raise RuntimeError(f"Could not resolve Windows shell folder {csidl}")
    return Path(buf.value)


def installed_processes():
    expected=os.path.normcase(str(INSTALL/"CoD2ChatTranslatorQt.exe"))
    return [proc for proc in psutil.process_iter(["exe"])
            if os.path.normcase(proc.info.get("exe") or "")==expected]


def launch_shortcut(path, name):
    assert path.is_file(), f"Missing installed {name} shortcut: {path}"
    assert not installed_processes(), "Previous installed process still active"
    profile_name = "CoD2ChatTranslator" if CANDIDATE else "CoD2ChatTranslatorQtPreview"
    default_settings=Path(os.environ["APPDATA"])/profile_name/"qt_settings.json"
    before=json.loads(default_settings.read_text(encoding="utf-8-sig"))
    os.startfile(str(path))
    try:
        def find_window():
            for proc in installed_processes():
                for native in DESKTOP.windows(process=proc.pid):
                    if native.is_visible() and "CoD2 Chat Translator" in native.window_text():
                        return proc,native
            return None
        proc,native=wait_for(find_window,f"{name} actual installed shortcut",45)
        cfg=json.loads(default_settings.read_text(encoding="utf-8-sig"))
        assert cfg["qt_admin_policy_version"]==1 and cfg["qt_always_admin"] is True
        assert elevated(proc.pid)=="True",f"{name}: installed EXE token not elevated"
        for row in before.get("server_monitor",{}).get("servers",[]):
            assert record(cfg,row["address"])==row, f"{name}: startup lost server {row}"
        assert cfg.get("server_monitor",{}).get("friends")==before.get("server_monitor",{}).get("friends")
        save_capture(native,"shortcut_"+name)
        native.close()
        proc.wait(timeout=25)
        assert not installed_processes(), f"{name}: installed process did not close"
        return {"shortcut":str(path.name),"token_elevated":True,
                "startup_policy":True,"server_and_friends_preserved":True}
    finally:
        for proc in installed_processes():
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except psutil.NoSuchProcess:
                pass


shortcut_name = ("CoD2 Chat Translator" if CANDIDATE else "CoD2 Chat Translator Qt Preview") + ".lnk"
shortcuts=[
    launch_shortcut(shell_folder(0x10)/shortcut_name,"desktop"),
    launch_shortcut(shell_folder(0x02)/shortcut_name,"start_menu"),
]

(EVIDENCE/"native_startup_policy.json").write_text(json.dumps({
    "previous_release":"9924b7e304a0" if PREVIOUS is not None else None,
    "previous_false_migrated":True,
    "upgraded":upgraded_policy,"clean":clean_policy,"shortcuts":shortcuts,
    "opt_out_persisted_across_reopen":True,
    "runner_token_elevated":elevated(os.getpid()),
    "interactive_uac_consent_and_real_game":"not exercised"
},indent=2),encoding="utf-8")

(EVIDENCE/"native_ui_upgrade.json").write_text(json.dumps({
    "old_release":"9333bb561122" if CANDIDATE else "c9ec1acd8ca2","legacy_required_explicit_save":True,
    "server_entered_through_ui":SERVER,"friend_entered_through_ui":FRIEND,
    "reopen_upgrade_reinstall":True,"new_autosave_without_save_button":True,
    "native_uac_gameplay":"not exercised"
},indent=2),encoding="utf-8")
