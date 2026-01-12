import contextlib
import html as html_module  # HTML実体参照のデコード用
import json
import os
import re
from datetime import datetime, timezone
from typing import Any

# 設定: 入力ファイル名と出力ファイル名とサイズ制限
INPUT_JSON_FILE = 'MyActivity.json'
OUTPUT_MD_FILE = 'Gemini_History.md'
MD_FILE_SIZE_LIMIT = 1500000  # 1.5MB
LAST_ENTRY_TIME_FILE = 'last_entry_time.txt'

def load_json(filepath: str) -> list[dict[str, Any]]:
    """JSONファイルを読み込む"""
    if not os.path.exists(filepath):
        print(f"エラー: ファイルが見つかりません: {filepath}")
        return []

    with open(filepath, encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSONデコードエラー: {e}")
            return []

def decode_unicode_escapes(s: str) -> str:
    """Unicodeエスケープシーケンスをデコード"""
    def repl(match):
        return chr(int(match.group(1), 16))
    return re.sub(r'\\u([0-9a-fA-F]{4})', repl, s)

def html_to_markdown(html_str: str) -> str:
    """
    簡易的なHTML -> Markdown/Text変換
    HTMLタグを取り除き、可読性のあるテキストに整形する
    """
    if not html_str:
        return ""

    # 1. Unicodeエスケープのデコード
    text = decode_unicode_escapes(html_str)

    # 2. HTML実体参照（&amp;など）のデコード
    text = html_module.unescape(text)

    # 3. 主要なタグをMarkdown風の記号や改行に置換
    # 見出し (h1-h6) -> **見出し** + 改行
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n**\1**\n', text, flags=re.IGNORECASE)

    # リストアイテム (li) -> ・ + 改行
    text = re.sub(r'<li[^>]*>', r'\n- ', text, flags=re.IGNORECASE)

    # 段落 (p), 行区切り (div), 改行 (br) -> 改行
    text = re.sub(r'</p>', r'\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', r'\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', r'\n', text, flags=re.IGNORECASE)

    # 太字 (b, strong) -> **文字**
    text = re.sub(r'<(b|strong)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE)

    # 4. その他のHTMLタグをすべて削除（タグの中身は残す）
    text = re.sub(r'<[^>]+>', '', text)

    # 5. 連続する空行を整理（3つ以上の改行を2つに）
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def extract_text_content(entry: dict[str, Any], last_entry_time_loaded: datetime) -> tuple[datetime, str]:
    """エントリからMarkdown形式のテキストコンテンツを抽出"""

    # 日時の抽出とフォーマット
    time_str = entry.get('time', '')
    dt: datetime = datetime.min.replace(tzinfo=timezone.utc)  # デフォルト値
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        if dt <= last_entry_time_loaded:
            return dt, ""  # 既に処理済みのエントリはスキップ
        formatted_date = dt.strftime('%Y/%m/%d %H:%M:%S')
    except ValueError:
        formatted_date = time_str

    md_output = f"## {formatted_date}\n\n"

    # 1. Action (タイトル)
    title = entry.get('title', '')
    if title:
        md_output += f"**Action**: {title}\n\n"

    # 2. User Prompt (subtitles) - 先に出力する
    subtitles = entry.get('subtitles', [])
    if subtitles:
        for item in subtitles:
            name = item.get('name', 'User')
            value = item.get('value', '')
            if value:
                # Markdown形式に整形
                md_output += f"### {name}\n"
                formatted_value = value.replace(chr(10), '  \n') # 改行コードをMarkdown用置換
                md_output += f"{formatted_value}\n\n"

    # 3. Gemini Response (safeHtmlItem) - 後に出力する
    safeHtmlItem = entry.get('safeHtmlItem', [])
    if safeHtmlItem:
        response_text = ""
        for item in safeHtmlItem:
            html = item.get('html', '')
            if html:
                # HTMLをテキスト/Markdownに変換して結合
                converted_text = html_to_markdown(html)
                response_text += converted_text + "\n\n"

        # 中身がある場合のみヘッダーと一緒に出力
        if response_text.strip():
            md_output += "### Gemini (Response)\n"
            md_output += f"{response_text}\n"

    md_output += "---\n\n" # セパレータ
    return dt, md_output

def main() -> None:
    try:
        print(f"処理開始: {INPUT_JSON_FILE} を読み込んでいます...")

        data = load_json(INPUT_JSON_FILE)
        if not data:
            return

        # "Gemini" 関連のアクティビティのみにフィルタリング
        gemini_entries: list[dict[str, Any]] = [
            entry for entry in data
            if "Gemini" in entry.get('header', '')
        ]

        print(f"{len(data)} 件中、Gemini の履歴 {len(gemini_entries)} 件を抽出しました。")
        print("Markdown への変換を実行中...")

        gemini_entries.reverse()

        last_entry_time_loaded: datetime = datetime.min.replace(tzinfo=timezone.utc)
        last_entry_time_processed: datetime = datetime.min.replace(tzinfo=timezone.utc)
        if os.path.exists(LAST_ENTRY_TIME_FILE):
            with open(LAST_ENTRY_TIME_FILE, encoding='utf-8') as f:
                time_str = f.read().strip()
                with contextlib.suppress(ValueError):
                    last_entry_time_loaded = datetime.fromisoformat(time_str)

        base_name, ext = os.path.splitext(OUTPUT_MD_FILE)

        def get_output_filename(idx: int) -> str:
            return f"{base_name}-{idx:02d}{ext}"

        file_index = 1
        is_append_mode = False
        while os.path.exists(get_output_filename(file_index)):
            is_append_mode = True
            file_index += 1
            output_filename = get_output_filename(file_index)
        if file_index > 1:
            file_index -= 1  # 最後に存在したファイルから続ける
        output_filename = get_output_filename(file_index)
        current_file_size = 0
        if is_append_mode:
            current_file_size = os.path.getsize(output_filename)

        header = "# Gemini Chat History Archive\n\n"
        header += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        def write_file(output_filename: str, header: str, texts: list[str], is_append_mode: bool) -> None:
            mode = 'a' if is_append_mode else 'w'
            with open(output_filename, mode, encoding='utf-8') as f:
                f.write(header)
                for text in texts:
                    f.write(text)

        texts = []
        current_file_size += len(header.encode('utf-8'))

        for _, entry in enumerate(gemini_entries):
            dt, text = extract_text_content(entry, last_entry_time_loaded)
            if text == "":
                continue
            last_entry_time_processed = dt
            text_size = len(text.encode('utf-8'))

            if current_file_size + text_size > MD_FILE_SIZE_LIMIT:
                if texts: # 書き込み対象がある場合のみ書き込む
                    write_file(output_filename, header, texts, is_append_mode)
                file_index += 1
                output_filename = get_output_filename(file_index)
                is_append_mode = False
                texts = []
                current_file_size = len(header.encode('utf-8'))

            texts.append(text)
            current_file_size += text_size

        if texts:
            write_file(output_filename, header, texts, is_append_mode)

        with open(LAST_ENTRY_TIME_FILE, 'w', encoding='utf-8') as f:
            f.write(last_entry_time_processed.isoformat())

        print(f"✅ 完了しました:{last_entry_time_loaded} より後の {last_entry_time_processed} までの履歴を"
              f" {file_index} ファイルに分割保存しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == '__main__':
    main()
