import json
import unittest
from pathlib import Path

import app


class BrandingTests(unittest.TestCase):
    def test_v1111_branding(self):
        self.assertEqual(app.APP_VERSION, "1.11.1")
        self.assertEqual(app.PROJECT_AUTHOR, "kriskarter")
        self.assertEqual(app.PROJECT_PROFILE_URL, "https://github.com/kriskarter")
        self.assertEqual(app.UI_STRINGS["ru"]["about"], "О программе")
        self.assertEqual(app.UI_STRINGS["en"]["about"], "About")

    def test_release_config_keeps_developer_metadata(self):
        root = Path(__file__).resolve().parents[1]
        cfg = json.loads((root / "release_config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["developer"], "kriskarter")
        self.assertEqual(cfg["developer_url"], "https://github.com/kriskarter")


if __name__ == "__main__":
    unittest.main()
