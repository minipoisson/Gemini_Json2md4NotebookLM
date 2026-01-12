# Gemini Json2md for NotebookLM

[日本語版READMEはこちら](README.ja.md)

This script converts Gemini history data exported via Google Takeout (default: `MyActivity.json`) into sequential Markdown files (default: `Gemini_History-00.md`) that are easy to import into NotebookLM.

## Features
- Removes HTML tags and formats as Markdown
- Automatically splits files considering NotebookLM's character limit (default: 1.5MB)
- Supports incremental updates (managed with `last_entry_time.txt`)

# Dependencies
No external dependencies required (Standard Library only)

## Usage

1. Download your "My Activity" data from Google Takeout in JSON format.
2. Place the extracted `MyActivity.json` in the same directory as this script.
3. Run the script:
   ```bash
   python convert_history.py [input_file] [output_file] [--limit SIZE]
   ```
   - `input_file` (default: MyActivity.json): The Google Takeout JSON file to import
   - `output_file` (default: Gemini_History.md): The output Markdown file name (sequentially numbered if split)
   - `--limit` (default: 1500000): Maximum file size for splitting (in bytes)

   Example:
   ```bash
   python convert_history.py MyActivity.json Gemini_History.md --limit 2000000
   ```
4. Upload the generated or updated Gemini_History-xx.md files to NotebookLM.

## License
See the LICENSE file in this repository for license details.
