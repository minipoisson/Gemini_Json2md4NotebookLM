import argparse
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import convert_history


class OutputStreamTests(unittest.TestCase):
    def test_progress_messages_are_written_to_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "Gemini_History.md")
            last_entry_time_file = os.path.join(tmpdir, "last_entry_time.txt")

            valid_entry = {
                "header": "Gemini - Test Conversation",
                "time": "2026-06-01T00:00:01Z",
            }

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with patch("convert_history.get_system_language", return_value="en"), patch(
                "convert_history.load_json", return_value=[valid_entry]
            ), patch("argparse.ArgumentParser.parse_args") as mock_args, patch(
                "convert_history.LAST_ENTRY_TIME_FILE", last_entry_time_file
            ):
                mock_args.return_value = argparse.Namespace(
                    input_file="dummy.json",
                    output_file=output_file,
                    limit=1000000,
                )

                with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                    result = convert_history.main()

            stdout = stdout_buffer.getvalue()

            self.assertEqual(result, 0)
            self.assertIn("Starting processing: Loading dummy.json", stdout)
            self.assertIn("Extracted 1 entries", stdout)
            self.assertIn("Converting to Markdown", stdout)
            self.assertIn("Chat histories written to file", stdout)
            self.assertIn("Completed:", stdout)
            self.assertEqual(stderr_buffer.getvalue(), "")

    def test_runtime_errors_are_written_to_stderr(self) -> None:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with patch("convert_history.get_system_language", return_value="en"), patch(
            "convert_history.load_json", side_effect=RuntimeError("Test error")
        ), patch(
            "argparse.ArgumentParser.parse_args"
        ) as mock_args:
            mock_args.return_value = argparse.Namespace(
                input_file="dummy.json",
                output_file="Gemini_History.md",
                limit=1000000,
            )

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                result = convert_history.main()

        self.assertEqual(result, 1)
        self.assertIn("An error occurred: Test error", stderr_buffer.getvalue())
        self.assertNotIn("An error occurred", stdout_buffer.getvalue())

    def test_warnings_are_written_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "Gemini_History.md")
            last_entry_time_file = os.path.join(tmpdir, "last_entry_time.txt")

            with open(last_entry_time_file, "w", encoding="utf-8") as f:
                f.write("not-a-timestamp")

            valid_entry = {
                "header": "Gemini - Test Conversation",
                "time": "2026-06-01T00:00:01Z",
            }

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with patch("convert_history.get_system_language", return_value="en"), patch(
                "convert_history.load_json", return_value=[valid_entry]
            ), patch(
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
            self.assertIn(
                "Warning: Invalid timestamp in last_entry_time.txt",
                stderr_buffer.getvalue(),
            )
            self.assertNotIn("Warning: Invalid timestamp", stdout_buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
