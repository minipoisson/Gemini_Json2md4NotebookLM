import unittest
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

    def test_detects_en_us_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("en_US", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "en")

    def test_falls_back_to_en_for_unknown_locale(self) -> None:
        with mock.patch("locale.getlocale", return_value=("xx_YY", "UTF-8")):
            self.assertEqual(convert_history.get_system_language(), "en")


if __name__ == "__main__":
    unittest.main()
