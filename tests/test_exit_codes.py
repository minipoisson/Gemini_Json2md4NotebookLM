import argparse
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import convert_history


class ExitCodeTests(unittest.TestCase):
    def test_main_returns_1_when_load_json_returns_empty_list(self) -> None:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with patch("convert_history.load_json", return_value=[]), patch(
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

    def test_main_returns_1_when_load_json_raises_runtime_error(self) -> None:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with patch(
            "convert_history.load_json", side_effect=RuntimeError("Test error")
        ), patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = argparse.Namespace(
                input_file="dummy.json",
                output_file="Gemini_History.md",
                limit=1000000,
            )

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                result = convert_history.main()

        self.assertEqual(result, 1)

    def test_main_returns_0_on_successful_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "Gemini_History.md")
            last_entry_time_file = os.path.join(tmpdir, "last_entry_time.txt")

            valid_entry = {
                "header": "Gemini - Test Conversation",
                "time": "2026-06-01T00:00:01Z",
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


if __name__ == "__main__":
    unittest.main()
