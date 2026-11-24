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
                       "_max_messages_changed",
                       "_background_only_changed","_compact_background_changed",
                       "_fade_changed","minimal_preset","readable_preset",
                       "text_only_preset","reset_overlay_position","test_overlay",
                       "clear_overlay","toggle_overlay_edit","_export_knowledge",
                       "capture_game_screenshot","check_updates"):
            self.assertIn(method,UI)
        self.assertIn("self.app.language_combo.bind(",UI)
        self.assertIn("styles_input.bind(",UI)
        self.assertIn("<<ComboboxSelected>>",UI)
        self.assertIn("textvariable=self.app.outgoing_chat.route_var",UI)
        self.assertIn("textvariable=self.app.max_messages_var",UI)

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

    def test_rc3_cinematic_brand_icons_and_compact_controls(self):
        for name,size in (
            ("brand_logo.png",(790,134)),
            ("brand_logo_compact.png",(708,120)),
            ("server_scene_thumb.png",(190,86)),
            ("version_plate.png",(125,45)),
            ("switch_on.png",(52,24)),
            ("switch_off.png",(52,24)),
            ("body_backdrop.png",(1500,780)),
        ):
            data=(ASSETS/name).read_bytes()
            self.assertEqual(data[:8],b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II",data[16:24]),size)
        for icon in ("test","clear","configure","screenshot","export","updates"):
            self.assertTrue((ASSETS/("quick_"+icon+".png")).exists())
        self.assertIn('image=ui_photo(parent,"switch_off.png")',UI)
        self.assertIn('selectimage=ui_photo(parent,"switch_on.png")',UI)
        self.assertIn("self._nav_font_size",UI)
        self.assertIn("self.home_scrollbar=bar",UI)
        self.assertIn("content.winfo_reqheight()",UI)
        self.assertIn('"brand_logo_compact.png"',UI)
        self.assertIn('"body_backdrop.png"',UI)
        self.assertIn("root.tk.call",UI)
        # The original game message parser and translation engine remain
        # separate; the design module must not issue new network requests.
        self.assertNotIn("requests.get(",UI)

    def test_no_fabricated_connection_state(self):
        for claim in ('"Подключено"','"Online"',"24 мс","FPS:"):
            self.assertNotIn(claim,UI)
        self.assertIn("self.server_var",UI)
        self.assertIn('app.config.get("experience_cache")',UI)
        self.assertIn('app.config.get("experience_collect")',UI)
        self.assertIn("runtime.pack.count",(ROOT/"dashboard_ui.py").read_text(encoding="utf-8"))

    def test_version_increment_without_translation_rewrite(self):
        self.assertIn('APP_VERSION = "1.21.1"',APP)
        self.assertIn('MyAppVersion "1.21.1"',(ROOT/"installer/CoD2ChatTranslator.iss").read_text(encoding="utf-8"))
