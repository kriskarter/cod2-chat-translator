import unittest
from unittest.mock import patch

import update_client


class UpdateClientTests(unittest.TestCase):
    def test_version_comparison(self):
        self.assertTrue(update_client.is_newer('1.10.1', '1.10.0'))
        self.assertTrue(update_client.is_newer('v2.0.0', '1.99.9'))
        self.assertFalse(update_client.is_newer('1.10.0', '1.10.0'))
        self.assertFalse(update_client.is_newer('1.9.9', '1.10.0'))

    def test_release_manifest(self):
        api_release = {
            'tag_name': 'v1.11.1',
            'assets': [
                {'name': 'update.json', 'browser_download_url': 'https://example.invalid/update.json'},
                {'name': 'CoD2ChatTranslator_Update.zip', 'browser_download_url': 'https://example.invalid/update.zip'},
            ],
        }
        manifest = {
            'version': '1.11.1',
            'asset': 'CoD2ChatTranslator_Update.zip',
            'sha256': 'a' * 64,
            'notes_ru': 'Тест',
            'notes_en': 'Test',
        }
        with patch('update_client._get_json', side_effect=[api_release, manifest]):
            info = update_client.check_github_release('1.10.0', 'owner/repo')
        self.assertIsNotNone(info)
        self.assertEqual(info.version, '1.11.1')
        self.assertEqual(info.sha256, 'a' * 64)

    def test_no_update_for_same_version(self):
        api_release = {'tag_name': 'v1.10.0', 'assets': []}
        with patch('update_client._get_json', return_value=api_release):
            self.assertIsNone(update_client.check_github_release('1.10.0', 'owner/repo'))


if __name__ == '__main__':
    unittest.main()
