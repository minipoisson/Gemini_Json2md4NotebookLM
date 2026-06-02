import argparse
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from unittest.mock import patch

import convert_history


class LastEntryTimeHandlingTests(unittest.TestCase):
    def test_load_last_entry_time_naive_assumes_utc(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write("2026-06-01T12:00:00")
            path = tmp.name

        stderr_buffer = io.StringIO()
        try:
            with redirect_stderr(stderr_buffer):
                loaded, force_full_regeneration = convert_history.load_last_entry_time(path)
        finally:
            os.remove(path)

        self.assertFalse(force_full_regeneration)
        self.assertEqual(loaded.tzinfo, timezone.utc)
        self.assertNotEqual(stderr_buffer.getvalue(), "")

    def test_load_last_entry_time_invalid_switches_full_regeneration(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write("not-a-timestamp")
            path = tmp.name

        stderr_buffer = io.StringIO()
        try:
            with redirect_stderr(stderr_buffer):
                loaded, force_full_regeneration = convert_history.load_last_entry_time(path)
        finally:
            os.remove(path)

        self.assertTrue(force_full_regeneration)
        self.assertEqual(loaded, datetime.min.replace(tzinfo=timezone.utc))
        self.assertNotEqual(stderr_buffer.getvalue(), "")

    def test_main_full_regeneration_removes_existing_numbered_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "Gemini_History.md")
            stale_file_01 = os.path.join(tmpdir, "Gemini_History-01.md")
            stale_file_02 = os.path.join(tmpdir, "Gemini_History-02.md")
            last_entry_time_file = os.path.join(tmpdir, "last_entry_time.txt")

            with open(stale_file_01, "w", encoding="utf-8") as f:
                f.write("stale content 01")
            with open(stale_file_02, "w", encoding="utf-8") as f:
                f.write("stale content 02")
            with open(last_entry_time_file, "w", encoding="utf-8") as f:
                f.write("invalid-timestamp")

            valid_entry = {
                "header": "Gemini",
                "time": "2026-06-01T00:00:01Z",
                "title": "sample",
            }

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with patch("convert_history.load_json", return_value=[valid_entry]), patch(
                "argparse.ArgumentParser.parse_args"
            ) as mock_args, patch(
                "convert_history.LAST_ENTRY_TIME_FILE", last_entry_time_file
            ):
                mock_args.return_value = argparse.Namespace(
                    input_file="dummy.json",
                    output_file=output_file,
                    limit=1000000,
                )

                with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                    result = convert_history.main()

            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists(stale_file_01))
            self.assertFalse(os.path.exists(stale_file_02))

            with open(stale_file_01, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("# Gemini Chat History Archive", content)
            self.assertNotIn("stale content 01", content)


if __name__ == "__main__":
    unittest.main()
