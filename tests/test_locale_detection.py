import io
import unittest
from contextlib import redirect_stderr
from unittest import mock

import convert_history


class GetSystemLanguageTests(unittest.TestCase):
    def setUp(self) -> None:
        convert_history.get_system_language.cache_clear()

    def test_detects_zh_cn_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("zh_CN", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_CN")

    def test_detects_zh_tw_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("zh_TW", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_TW")

    def test_detects_zh_hans_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("zh-Hans", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_CN")

    def test_detects_zh_hant_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("zh-Hant", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_TW")

    def test_detects_chinese_china_locale_name(self) -> None:
        with mock.patch("locale.getlocale", return_value=("Chinese_China", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_CN")

    def test_detects_chinese_taiwan_locale_name(self) -> None:
        with mock.patch("locale.getlocale", return_value=("Chinese_Taiwan", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "zh_TW")

    def test_detects_en_us_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("en_US", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "en")

    def test_detects_language_name_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("English_United States", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "en")

    def test_falls_back_to_en_when_locale_is_none(self) -> None:
        with mock.patch("locale.getlocale", return_value=(None, None)):
            self.assertEqual(convert_history.get_system_language(), "en")

    def test_falls_back_to_en_for_unknown_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("xx_YY", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "en")

    def test_falls_back_to_en_when_getlocale_raises(self) -> None:
        stderr_buffer = io.StringIO()
        with mock.patch("locale.getlocale", side_effect=RuntimeError("locale failure")), redirect_stderr(
            stderr_buffer
        ):
            self.assertEqual(convert_history.get_system_language(), "en")

        self.assertIn("Error while detecting system language", stderr_buffer.getvalue())
        self.assertIn("locale failure", stderr_buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
