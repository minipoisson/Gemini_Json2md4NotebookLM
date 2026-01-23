# Gemini Json2md for NotebookLM
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/minipoisson/Gemini_Json2md4NotebookLM)
![Release](https://img.shields.io/github/v/release/minipoisson/Gemini_Json2md4NotebookLM)

[日本語版READMEはこちら](README.ja.md)

This script converts Gemini history data exported via Google Takeout (default: `MyActivity.json`) into sequential Markdown files (default: `Gemini_History-00.md`) that are easy to import into NotebookLM.

## Features
- Removes HTML tags and formats as Markdown
- Automatically splits files considering NotebookLM's character limit (default: 1.5MB)
- Supports incremental updates (managed with `last_entry_time.txt`)

## Dependencies
No external dependencies required (Standard Library only)

## Requirements
- Python 3.9 or higher

## Usage

1. Download your "My Activity" data from Google Takeout in JSON format.
2. Place the extracted `MyActivity.json` in the same directory as this script.
3. Run the script:
   ```bash
   python convert_history.py [--input_file FILE] [--output_file FILE] [--limit SIZE]
   ```
   - `--input_file` (default: MyActivity.json): The Google Takeout JSON file to import
   - `--output_file` (default: Gemini_History.md): The output Markdown file name (sequentially numbered)
   - `--limit` (default: 1500000): Maximum file size for splitting (in bytes)

   Example:
   ```bash
   python convert_history.py --input_file MyActivity.json --output_file Gemini_History.md --limit 2000000
   ```
4. Upload the generated or updated Gemini_History-xx.md files to NotebookLM.

## License
See the LICENSE file in this repository for license details.
