"""Contract checks for live tactical WWII Tk dashboard without requiring X11."""
import ast
import pathlib
import unittest

import app

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "dashboard_ui.py").read_text(encoding="utf-8")
MODULE = ast.parse(SOURCE)

def static_i18n():
    assignment = next(
        node for node in MODULE.body
        if isinstance(node, ast.Assign)
        and any(isinstance(x, ast.Name) and x.id == "I18N" for x in node.targets)
    )
    return ast.literal_eval(assignment.value)

class DashboardContractTests(unittest.TestCase):
    def test_ui_is_a_real_tk_module_and_no_screenshot_replaces_actions(self):
        self.assertTrue((ROOT / "dashboard_ui.py").exists())
        self.assertIn("class Dashboard:", SOURCE)
        self.assertIn("tk.Frame", SOURCE)
        self.assertIn("ttk.Combobox", SOURCE)
        self.assertIn("def build_dashboard(app):", SOURCE)
        self.assertNotIn("Screenshot mockup", SOURCE)
        self.assertIn("from wwii_dashboard import build_dashboard", (ROOT / "app.py").read_text(encoding="utf-8"))
        tactical=(ROOT/"wwii_dashboard.py").read_text(encoding="utf-8")
        self.assertIn("class WWIIDashboard(Dashboard):", tactical)
        self.assertIn("ui_photo(header,\"hero.png\")", tactical)
        self.assertIn('nav=tk.Frame(nav_shell,bg=SIDEBAR)', tactical)
        self.assertNotIn("sidebar.pack(side=\"left\"", tactical)
        self.assertIn('self._home_overlay_prefs', tactical)
        self.assertIn('self._home_quick', tactical)

    def test_all_localizations_cover_the_same_pages_and_labels(self):
        i18n = static_i18n()
        self.assertEqual(set(i18n), {"ru", "uk", "en"})
        keys = set(i18n["ru"])
        self.assertGreater(len(keys), 65)
        for lang in i18n:
            with self.subTest(language=lang):
                self.assertEqual(set(i18n[lang]), keys)
                self.assertTrue(all(isinstance(value, str) and value for value in i18n[lang].values()))
                for key in ("home", "translation", "overlay", "knowledge", "stats", "settings"):
                    self.assertIn(key, i18n[lang])

    def test_all_pages_and_real_backend_controls_remain_wired(self):
        for name in ("home", "translation", "overlay", "knowledge", "stats", "settings"):
            self.assertIn(f'self._{name}(self.pages["{name}"])', SOURCE)
        self.assertIn('lambda:self.navigate("knowledge")', SOURCE)
        self.assertIn('lambda:self.navigate("stats")', SOURCE)
        for callback in (
            "test_overlay", "clear_overlay", "toggle_overlay_edit",
            "enable_cod2_borderless", "capture_game_screenshot",
            "_launch_featured_server", "_open_featured_server_discord",
            "_check_knowledge_update",
            "_export_knowledge", "_clear_knowledge", "_persist_settings",
            "_outgoing_enabled_changed", "change_ui_language",
            "_background_slider", "_font_slider", "_ttl_slider",
            "_max_messages_changed", "_background_only_changed",
            "_compact_background_changed", "_fade_changed",
        ):
            self.assertIn(callback, SOURCE, callback)

    def test_no_invented_ping_fps_or_service_connected_claim(self):
        self.assertNotIn("24 мс", SOURCE)
        self.assertNotIn("8.4 MB", SOURCE)
        self.assertNotIn("Актуальная версия", SOURCE)
        self.assertIn("shared.snapshot()", SOURCE)
        self.assertIn("runtime.pack.count", SOURCE)
        self.assertIn("app.status_var", SOURCE)
        self.assertIn("app.server_summary_var", SOURCE)

    def test_style_luminance_has_readable_text_contrast(self):
        def rgb(code):
            return [int(code[i:i+2], 16)/255 for i in (1, 3, 5)]
        def luminance(code):
            v = rgb(code)
            v = [(c/12.92) if c <= .04045 else ((c+.055)/1.055)**2.4 for c in v]
            return sum(a*b for a,b in zip(v, (.2126,.7152,.0722)))
        def contrast(a,b):
            lo,hi = sorted((luminance(a),luminance(b)))
            return (hi+.05)/(lo+.05)
        colors = {}
        for node in MODULE.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("BG","SIDEBAR","CARD","TEXT","MUTED","CYAN","AMBER","GREEN"):
                        colors[target.id] = ast.literal_eval(node.value)
        for bg in ("BG","SIDEBAR","CARD"):
            for fg in ("TEXT","MUTED"):
                self.assertGreaterEqual(contrast(colors[bg],colors[fg]),4.5, f"{fg} on {bg}")
        self.assertGreaterEqual(contrast(colors["CARD"],colors["CYAN"]),4.5)
