# Gemini Json2md for NotebookLM
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/github/license/minipoisson/Gemini_Json2md4NotebookLM)
![Release](https://img.shields.io/github/v/release/minipoisson/Gemini_Json2md4NotebookLM)

Google Takeout でエクスポートした Gemini の履歴データ (規定値は `MyActivity.json`) を、NotebookLM に読み込ませやすい Markdown 形式の連番のファイル（規定値は `Gemini_History-00.md`）に変換するスクリプトです。

## 特徴
- HTMLタグを除去し、Markdown形式に整形
- NotebookLMの制限（文字数）を考慮してファイルを自動分割 (規定値は1.5MB)
- 差分更新に対応（`last_entry_time.txt` で管理）

## 依存関係
外部依存はありません（Python標準ライブラリのみで動作します）

## 必要要件
- Python 3.9 以上

## 使い方

1. Google Takeout から「マイ アクティビティ」のデータを JSON 形式でダウンロードする。
2. 解凍したフォルダ内の `MyActivity.json` をこのスクリプトと同じ階層に置く。
3. スクリプトを実行する。
   ```bash
   python convert_history.py [--input_file FILE] [--output_file FILE] [--limit SIZE]
   ```
   - `--input_file`（省略時: MyActivity.json）: 入力するGoogle TakeoutのJSONファイル名
   - `--output_file`（省略時: Gemini_History.md）: 出力するMarkdownファイル名（連番付きで出力）
   - `--limit`（省略時: 1500000）: 分割するファイルサイズ上限（バイト単位）

   例：
   ```bash
   python convert_history.py --input_file MyActivity.json --output_file Gemini_History.md --limit 2000000
   ```
4. 生成ないしは更新された Gemini_History-xx.md を NotebookLM にアップロードする。

## ライセンス
ライセンスについては本リポジトリの LICENSE ファイルをご参照ください。