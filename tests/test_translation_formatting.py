from __future__ import annotations

import io
import string
import unittest
from contextlib import redirect_stderr

import convert_history


class TranslationFormattingTests(unittest.TestCase):
    def test_translation_placeholders_match_english_reference(self) -> None:
        formatter = string.Formatter()
        english_map = convert_history.TRANSLATIONS["en"]

        def parse_fields(template: str) -> list[tuple[str | None, str | None, str | None]]:
            return [
                (field_name, format_spec, conversion)
                for _, field_name, format_spec, conversion in formatter.parse(template)
                if field_name is not None
            ]

        for lang, messages in convert_history.TRANSLATIONS.items():
            for key, english_template in english_map.items():
                with self.subTest(lang=lang, key=key):
                    self.assertIn(key, messages)
                    self.assertEqual(parse_fields(messages[key]), parse_fields(english_template))

    def test_translate_for_lang_falls_back_to_english_when_localized_format_is_invalid(self) -> None:
        original_ja = convert_history.TRANSLATIONS["ja"]["start_processing"]

        try:
            convert_history.TRANSLATIONS["ja"]["start_processing"] = "{"  # Invalid format string
            stderr_buffer = io.StringIO()
            with redirect_stderr(stderr_buffer):
                result = convert_history.translate_for_lang("ja", "start_processing", "sample.json")

            expected = convert_history.TRANSLATIONS["en"]["start_processing"].format("sample.json")
            self.assertEqual(result, expected)
            self.assertIn("Failed to format translation", stderr_buffer.getvalue())
        finally:
            convert_history.TRANSLATIONS["ja"]["start_processing"] = original_ja

    def test_translate_for_lang_returns_original_message_if_localized_and_english_formats_fail(self) -> None:
        original_ja = convert_history.TRANSLATIONS["ja"]["start_processing"]
        original_en = convert_history.TRANSLATIONS["en"]["start_processing"]

        try:
            convert_history.TRANSLATIONS["ja"]["start_processing"] = "{"  # Invalid format string
            convert_history.TRANSLATIONS["en"]["start_processing"] = "{"  # Invalid fallback format string
            stderr_buffer = io.StringIO()
            with redirect_stderr(stderr_buffer):
                result = convert_history.translate_for_lang("ja", "start_processing", "sample.json")

            self.assertEqual(result, "{")
            self.assertIn("English fallback also failed", stderr_buffer.getvalue())
        finally:
            convert_history.TRANSLATIONS["ja"]["start_processing"] = original_ja
            convert_history.TRANSLATIONS["en"]["start_processing"] = original_en


if __name__ == "__main__":
    unittest.main()
