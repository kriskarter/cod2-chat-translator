"""Real desktop smoke test for the Modern Esports dashboard (requires Tk/X display).

Examples:
    xvfb-run -a python tools/dashboard_smoke.py
    xvfb-run -a python tools/dashboard_smoke.py --screenshot /tmp/dashboard.png

This uses an isolated temporary configuration, not a player's saved settings.
Screenshot is a REAL running Tk window, not a static mockup.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", type=Path)
    parser.add_argument("--preview-width",type=int,default=1320)
    parser.add_argument("--preview-height",type=int,default=840)
    parser.add_argument("--tk-scaling",type=float,default=None,
                        help="Optional Tk font/UI scale probe (not native Windows DPI)")
    parser.add_argument("--require-fit",action="store_true",
                        help="Assert all Home controls fit viewport without vertical scrolling")
    args = parser.parse_args()
    if not 1050 <= args.preview_width <= 2500 or not 650 <= args.preview_height <= 1600:
        parser.error("Preview geometry is outside supported bounds")
    with tempfile.TemporaryDirectory(prefix="cod2-dashboard-test-") as temp:
        os.environ["APPDATA"] = temp
        os.environ["XDG_CONFIG_HOME"] = temp
        # Never inherit an existing local player's configuration or cached
        # examples, even if the same computer is running the smoke test.
        import tkinter as tk
        from tkinter import ttk
        from app import ControlApp, APP_VERSION, TARGET_LANGUAGES

        root = tk.Tk()
        if args.tk_scaling is not None:
            if not 1.0 <= args.tk_scaling <= 2.5:
                parser.error("tk-scaling must be between 1.0 and 2.5")
            root.tk.call("tk", "scaling", args.tk_scaling)
        app = None
        try:
            app = ControlApp(root)
            app.overlay.set_visible(False)
            root.update_idletasks()
            root.update()
            dashboard = app.dashboard
            expected = ("home", "translation", "overlay", "knowledge", "stats", "settings")
            assert all(key in dashboard.pages for key in expected)
            assert root.winfo_width() >= 1050
            assert len(dashboard.nav_buttons) == 7
            assert app.language_combo.winfo_exists()
            assert app.overlay_edit_button.winfo_exists()
            assert app.overlay_edit_button_alt.winfo_exists()

            # Click actual horizontal buttons, not only the internal
            # page-switch method. Auxiliary actions remain wired but are
            # not invoked because server/Discord/update are external.
            for key,expected_page in (
                ("knowledge","knowledge"),("stats","stats"),
                ("settings","settings"),("home","home"),
            ):
                dashboard.nav_buttons[key].invoke()
                root.update_idletasks()
                root.update()
                assert dashboard.page == expected_page

            for page in expected:
                assert dashboard.navigate(page), page
                root.update_idletasks()
                root.update()
                assert dashboard.page == page
                assert dashboard.pages[page].winfo_ismapped()

            # Actual user control (not just manually modifying a config
            # variable): a Tk button .invoke() calls the existing callback.
            assert dashboard.navigate("knowledge")
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            collection = next(
                w for w in descendants(dashboard.pages["knowledge"])
                if isinstance(w, (tk.Checkbutton,ttk.Checkbutton)) and any(
                    phrase in w.cget("text").casefold()
                    for phrase in ("собирать примеры", "collect local examples")
                )
            )
            old_value = app.experience.collect
            collection.invoke()
            root.update()
            assert app.experience.collect != old_value
            collection.invoke()
            root.update()
            assert app.experience.collect == old_value

            # Exercise the actual image-backed F8/F9 native switches,
            # not just the shared BooleanVar in Python.
            assert dashboard.navigate("home")
            for caption,variable in (
                ("F8",app.enabled_var),
                ("F9",app.outgoing_chat.enabled_var),
            ):
                switch=next(
                    w for w in descendants(dashboard.pages["home"])
                    if isinstance(w,tk.Checkbutton) and w.cget("text")==caption
                )
                before=bool(variable.get())
                switch.invoke()
                root.update()
                assert bool(variable.get())!=before,caption
                switch.invoke()
                root.update()
                assert bool(variable.get())==before,caption

            app.smart_engine_var.set(False)
            app._persist_settings()
            dashboard.refresh()
            assert dashboard.engine_var.get() == "Classic"
            app.smart_engine_var.set(True)
            app._persist_settings()
            dashboard.refresh()
            assert dashboard.engine_var.get() in ("Smart V1", "Smart V2")

            # Real overlay edit state and both action labels must match.
            app.toggle_overlay_edit()
            assert app.overlay_editing
            assert app.overlay_edit_button.cget("text") == app.t("lock_overlay")
            assert app.overlay_edit_button_alt.cget("text") == app.t("lock_overlay")
            app.toggle_overlay_edit()
            assert not app.overlay_editing
            assert app.overlay_edit_button_alt.cget("text") == app.t("configure_overlay")
            app.overlay.set_visible(False)

            for ui, language in (("Українська","uk"),("English","en"),("Русский","ru")):
                app.ui_language_var.set(ui)
                app.change_ui_language()
                root.update()
                assert app.ui_language == language
                assert app.dashboard.navigate("translation")
                assert app.language_combo.winfo_exists()
                assert app.dashboard.navigate("knowledge")
                assert app.dashboard.navigate("stats")
                assert app.dashboard.navigate("settings")
                assert app.dashboard.navigate("home")

            # Rebuilding localized controls should not reset a custom
            # window size or unexpectedly send the user back to Home.
            root.geometry("1150x750")
            root.update_idletasks()
            root.update()
            assert app.dashboard.navigate("knowledge")
            app.ui_language_var.set("English")
            app.change_ui_language()
            root.update_idletasks()
            root.update()
            assert root.winfo_width() == 1150
            assert root.winfo_height() == 750
            assert app.dashboard.page == "knowledge"
            app.ui_language_var.set("Русский")
            app.change_ui_language()
            root.update_idletasks()
            root.update()
            assert app.dashboard.page == "knowledge"

            root.geometry("1050x690")
            root.update_idletasks()
            root.update()
            assert root.winfo_width() == 1050
            assert app.dashboard.navigate("translation")
            assert app.dashboard.navigate("overlay")
            assert app.dashboard.navigate("home")

            root.geometry(f"{args.preview_width}x{args.preview_height}")
            root.update_idletasks()
            root.update()
            app.overlay.set_visible(False)
            app.dashboard.navigate("home")
            root.update()
            content_height=app.dashboard.home_content.winfo_reqheight()
            viewport_height=app.dashboard.home_canvas.winfo_height()
            has_bar=bool(app.dashboard.home_scrollbar.winfo_manager())
            print(
                "HOME_LAYOUT",
                f"{root.winfo_width()}x{root.winfo_height()}",
                "content",content_height,
                "viewport",viewport_height,
                "scrollbar",has_bar,
                "scaling",root.tk.call("tk","scaling"),
                flush=True
            )
            if args.require_fit:
                assert content_height <= viewport_height+3, (
                    f"Home does not fit: {content_height} > {viewport_height}")
                assert not has_bar, "Unexpected Home scrollbar"
            if args.screenshot:
                # Only take a screenshot when an X11 server and ffmpeg are
                # explicitly provided. No screenshots are sent anywhere.
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                if sys.platform != "linux":
                    print("Screenshot capture is only supported via X11 ffmpeg", file=sys.stderr)
                else:
                    subprocess.run([
                        "ffmpeg","-hide_banner","-loglevel","error",
                        "-f","x11grab","-draw_mouse","0","-video_size",
                        f"{args.preview_width}x{args.preview_height}",
                        "-i",os.environ["DISPLAY"],"-frames:v","1",
                        "-update","1","-y",str(args.screenshot)
                    ], check=True, timeout=15)
            print(f"DASHBOARD SMOKE PASS: v{APP_VERSION}, pages=6, nav=7,"
                  " settings callbacks, overlay state, RU/UK/EN, 1050px layout")
            return 0
        finally:
            if app is not None:
                app.close()
            else:
                root.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
