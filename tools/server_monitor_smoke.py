"""Exercise live Tk server dialogs and persistence in an isolated config."""
from __future__ import annotations
import os
import tempfile
import tkinter as tk
from tkinter import ttk


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def main():
    with tempfile.TemporaryDirectory(prefix="cod2-monitor-smoke-") as temp:
        os.environ["APPDATA"]=temp
        os.environ["XDG_CONFIG_HOME"]=temp
        from app import ControlApp, load_config
        root=tk.Tk()
        app=ControlApp(root)
        app.overlay.set_visible(False)
        root.update()
        page=app.dashboard.server_page
        def edit_dialog(address,label):
            def submit():
                dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel)
                            and w.title() in ("Сервер CoD2","CoD2 server"))
                fields=[w for w in descendants(dialog) if isinstance(w,ttk.Entry)]
                assert len(fields)>=2
                for widget,value in zip(fields,(address,label)):
                    widget.delete(0,"end");widget.insert(0,value)
                save=next(w for w in descendants(dialog) if isinstance(w,ttk.Button)
                          and w.cget("text") in ("Сохранить","Save"))
                save.invoke()
            root.after(120,submit)
        try:
            for port in (28960,28961):
                edit_dialog(f"127.0.0.1:{port}",f"Local {port}")
                page.add()
            addresses=[entry["address"] for entry in load_config()["server_monitor"]["servers"]]
            assert "146.59.34.100:28960" in addresses
            assert "127.0.0.1:28960" in addresses and "127.0.0.1:28961" in addresses
            page.listbox.selection_clear(0,"end")
            index=next(i for i,s in enumerate(page._visible) if s.address=="127.0.0.1:28961")
            page.listbox.selection_set(index)
            edit_dialog("127.0.0.1:28962","Renamed local")
            page.edit()
            assert any(s.label=="Renamed local" and s.address=="127.0.0.1:28962"
                       for s in app.monitor_settings["servers"])
            persisted=load_config()["server_monitor"]
            assert any(s["address"]=="127.0.0.1:28962" for s in persisted["servers"])
            assert not any(s["address"]=="127.0.0.1:28961" for s in persisted["servers"])
            print("SERVER MONITOR UI PASS: 2 dialog additions, edit, config roundtrip")
        finally:
            app.close()


if __name__=="__main__":
    main()
