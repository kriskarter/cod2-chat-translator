"""Offline contract for selected 1944-style metal rebrand and real actions."""
import pathlib
import struct
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
UI=(ROOT/"wwii_dashboard.py").read_text(encoding="utf-8")
APP=(ROOT/"app.py").read_text(encoding="utf-8")
ASSETS=ROOT/"assets/ui_wwii"

class WWIIContractTests(unittest.TestCase):
    def test_real_wwii_dashboard_replaces_rejected_sidebar(self):
        self.assertIn("from wwii_dashboard import build_dashboard",APP)
        self.assertIn("class WWIIDashboard(Dashboard):",UI)
        self.assertIn("nav_shell=tk.Frame",UI)
        self.assertIn("nav=tk.Frame",UI)
        self.assertNotIn("sidebar.pack(",UI)
        for name in ("home","knowledge","stats","settings","updates","discord","about"):
            self.assertIn('"'+name+'"',UI)
            self.assertTrue((ASSETS/("nav_"+name+".png")).exists())

    def test_six_main_sections_and_real_callbacks(self):
        for method in ("_home_server","_home_engine","_home_translation",
                       "_home_overlay","_home_overlay_prefs","_home_quick"):
            self.assertIn("self."+method,UI)
        for method in ("_launch_featured_server","_open_featured_server_discord",
                       "toggle_enabled","_outgoing_enabled_changed",
                       "_persist_settings","toggle_original",
                       "_font_slider","_background_slider","_ttl_slider",
                       "_background_only_changed","_compact_background_changed",
                       "_fade_changed","minimal_preset","readable_preset",
                       "text_only_preset","reset_overlay_position","test_overlay",
                       "clear_overlay","toggle_overlay_edit","_export_knowledge",
                       "capture_game_screenshot","check_updates"):
            self.assertIn(method,UI)
        self.assertIn('self.app.language_combo.bind("<<ComboboxSelected>>"',UI)
        self.assertIn('style_combo.bind("<<ComboboxSelected>>"',UI)

    def test_texture_and_header_photos_bundled_as_data(self):
        for name,w,h in (("hero.png",1500,166),("server_scene.png",255,120),
                         ("plate.png",1024,52),("panel.png",1024,350)):
            data=(ASSETS/name).read_bytes()
            self.assertEqual(data[:8],b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II",data[16:24]),(w,h))
            self.assertLess(len(data),1_500_000)
        self.assertTrue((ASSETS/"source_coutances.jpg").exists())
        credit=(ASSETS/"README.md").read_text(encoding="utf-8")
        self.assertIn("public domain",credit.lower())
        self.assertIn("Wikimedia Commons",credit)
        self.assertIn("PhotoImage",(ROOT/"dashboard_ui.py").read_text(encoding="utf-8"))

    def test_no_fabricated_connection_state(self):
        for claim in ('"Подключено"','"Online"',"24 мс","FPS:"):
            self.assertNotIn(claim,UI)
        self.assertIn("self.server_var",UI)
        self.assertIn('app.config.get("experience_cache")',UI)
        self.assertIn('app.config.get("experience_collect")',UI)
        self.assertIn("runtime.pack.count",(ROOT/"dashboard_ui.py").read_text(encoding="utf-8"))

    def test_version_increment_without_translation_rewrite(self):
        self.assertIn('APP_VERSION = "1.21.0"',APP)
        self.assertIn('MyAppVersion "1.21.0"',(ROOT/"installer/CoD2ChatTranslator.iss").read_text(encoding="utf-8"))
