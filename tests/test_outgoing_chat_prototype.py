import unittest

from outgoing_chat_prototype import normalize_outgoing_text


class OutgoingChatPrototypeTests(unittest.TestCase):
    def test_normalizes_whitespace(self):
        self.assertEqual(
            normalize_outgoing_text("  привет   всем  "),
            "привет всем",
        )

    def test_preserves_cyrillic_and_punctuation(self):
        self.assertEqual(
            normalize_outgoing_text("спасибо, хороший выстрел :)"),
            "спасибо, хороший выстрел :)",
        )

    def test_multiline_input_becomes_single_chat_line(self):
        self.assertEqual(
            normalize_outgoing_text("привет\nкак дела?"),
            "привет как дела?",
        )


if __name__ == "__main__":
    unittest.main()
