"""Offline contract for selected 1944-style metal rebrand and real actions."""
import pathlib
import struct
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
UI=(ROOT/"wwii_dashboard.py").read_text(encoding="utf-8")
HOME=(ROOT/"premium_home.py").read_text(encoding="utf-8")
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

    def test_beginner_home_and_expert_actions_remain_wired(self):
        self.assertIn("build_premium_home(self, page)",UI)
        self.assertIn("console_chassis.png",HOME)
        self.assertIn("generic_panel.png",HOME)
        self.assertNotIn("self._home_overlay_prefs",UI)
        for method in ("_launch_featured_server","_open_featured_server_discord",
                       "toggle_enabled","_outgoing_enabled_changed",
                       "_persist_settings","test_overlay",
                       "toggle_overlay_edit",
                       "capture_game_screenshot","check_updates"):
            self.assertIn(method,UI+HOME)
        self.assertIn("a.language_combo.bind(",HOME)
        self.assertIn("<<ComboboxSelected>>",HOME)
        self.assertIn("a.outgoing_chat.source_name_var",HOME)
        self.assertIn("a.outgoing_chat.target_name_var",HOME)
        self.assertIn('self.dashboard.navigate("overlay")',HOME)
        self.assertIn("service.add_command",UI)
        self.assertNotIn("extra_menu.add_command",UI)

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
        self.assertIn('image=ui_photo(parent,"premium_switch_off.png")',UI)
        self.assertIn('selectimage=ui_photo(parent,"premium_switch_on.png")',UI)
        self.assertIn("self._nav_font_size",UI)
        self.assertIn("home_scrollbar = bar",HOME)
        self.assertIn("content.winfo_reqheight()",HOME)
        self.assertIn('"premium_logo.png"',UI)
        self.assertIn('"premium_hero.png"',UI)
        for name in ("hero_source", "logo_source", "steel_source"):
            self.assertTrue((ROOT/"assets/ui_premium"/(name+".png")).exists())
        for group in ("metal", "amber"):
            for state in ("normal", "hover", "pressed", "disabled"):
                self.assertTrue((ASSETS/f"premium_{group}_{state}.png").exists())
        self.assertIn('style.element_create(element, "image"',
                      (ROOT/"dashboard_ui.py").read_text(encoding="utf-8"))
        for name in ("console_chassis.png", "generic_panel.png"):
            self.assertTrue((ROOT/"assets/ui_premium"/name).exists())
        self.assertIn("self.root.tk.call",UI)
        # The original game message parser and translation engine remain
        # separate; the design module must not issue new network requests.
        self.assertNotIn("requests.get(",UI)

    def test_no_fabricated_connection_state(self):
        for claim in ('"Подключено"','"Online"',"24 мс","FPS:"):
            self.assertNotIn(claim,UI)
        self.assertIn("FEATURED_SERVER.address",HOME)
        self.assertIn("self.engine_pack_label",UI)
        self.assertIn("runtime.pack.count",(ROOT/"dashboard_ui.py").read_text(encoding="utf-8"))

    def test_version_increment_without_translation_rewrite(self):
        self.assertIn('APP_VERSION = "1.21.3"',APP)
        self.assertIn('MyAppVersion "1.21.3"',(ROOT/"installer/CoD2ChatTranslator.iss").read_text(encoding="utf-8"))
