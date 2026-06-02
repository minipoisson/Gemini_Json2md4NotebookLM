"""
Gemini_Json2md4NotebookLM
Converts Gemini's exported MyActivity.json into sequential Markdown files
suitable for NotebookLM ingestion.

Usage:
    python convert_history.py \
        [--input_file MyActivity.json] \
        [--output_file Gemini_History.md] \
        [--limit 1000000]
"""

import argparse
import functools
import html as html_module
import json
import locale
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any

LAST_ENTRY_TIME_FILE = "last_entry_time.txt"

# TRANSLATIONSに含まれる言語名からISO 639-1コードへのマッピング辞書
LANG_MAP = {
    "Arabic": "ar",
    "Bengali": "bn",
    "German": "de",
    "English": "en",
    "Spanish": "es",
    "Persian": "fa",
    "French": "fr",
    "Hindi": "hi",
    "Indonesian": "id",
    "Japanese": "ja",
    "Javanese": "jv",
    "Korean": "ko",
    "Marathi": "mr",
    "Malay": "ms",
    "Punjabi": "pa",
    "Portuguese": "pt",
    "Russian": "ru",
    "Swahili": "sw",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Chinese_China": "zh_CN",
    "Chinese_Taiwan": "zh_TW",
}

TRANSLATIONS = {
    "ar": {
        "error_lang_detection": "خطأ أثناء اكتشاف لغة النظام: {}",
        "file_not_found": "خطأ: الملف غير موجود: {}",
        "json_decode_error": "خطأ في فك ترميز JSON: {}",
        "start_processing": "🚀 بدء المعالجة: جاري تحميل {}...",
        "extracted_entries": "تم استخراج {0} مدخلات، منها {1} هي سجل Gemini.",
        "converting_markdown": "جارٍ التحويل إلى Markdown...",
        "appended_to_file": "تمت إضافة سجلات الدردشة إلى الملف: {}",
        "written_to_file": "تم كتابة سجلات الدردشة إلى الملف: {}",
        "processing_complete": "✅ اكتمل: تم حفظ السجل من {0} إلى {1} في إجمالي {2} ملفات.",
        "error_occurred": "حدث خطأ: {}",
        "warning_last_entry_time_empty": "تحذير: الملف last_entry_time.txt فارغ. يتم الانتقال إلى وضع إعادة التوليد الكامل.",
        "warning_last_entry_time_invalid": "تحذير: طابع زمني غير صالح في last_entry_time.txt ({!r}). يتم الانتقال إلى وضع إعادة التوليد الكامل.",
        "warning_last_entry_time_naive": "تحذير: يحتوي last_entry_time.txt على طابع زمني بدون منطقة زمنية. سيتم اعتباره بتوقيت UTC.",
        "warning_removed_existing_outputs": "تحذير: تم إزالة {} من ملفات المخرجات الحالية قبل إعادة التوليد الكامل.",
    },
    "bn": {
        "error_lang_detection": "সিস্টেম ভাষা সনাক্তকরণে ত্রুটি: {}",
        "file_not_found": "ত্রুটি: ফাইল পাওয়া যায়নি: {}",
        "json_decode_error": "JSON ডিকোড ত্রুটি: {}",
        "start_processing": "🚀 প্রক্রিয়াকরণ শুরু হচ্ছে: {} লোড হচ্ছে...",
        "extracted_entries": "{0} এন্ট্রি বের করা হয়েছে, যার মধ্যে {1} টি Gemini ইতিহাস।",
        "converting_markdown": "Markdown এ রূপান্তর করা হচ্ছে...",
        "appended_to_file": "চ্যাট ইতিহাস ফাইলে যোগ করা হয়েছে: {}",
        "written_to_file": "চ্যাট ইতিহাস ফাইলে লেখা হয়েছে: {}",
        "processing_complete": "✅ সম্পন্ন: {0} থেকে {1} পর্যন্ত ইতিহাস মোট {2} ফাইলে সংরক্ষণ করা হয়েছে।",
        "error_occurred": "একটি ত্রুটি ঘটেছে: {}",
        "warning_last_entry_time_empty": "सतर्कता: last_entry_time.txt ফাইলটি খালি। সম্পূর্ণ পুনরুৎপাদন মোডে পরিবর্তন করা হচ্ছে।",
        "warning_last_entry_time_invalid": "सतर्कता: last_entry_time.txt-এ অবৈধ টাইমস্ট্যাম্প ({!r})। সম্পূর্ণ পুনরুৎপাদন মোডে পরিবর্তন করা হচ্ছে।",
        "warning_last_entry_time_naive": "सतर्कता: last_entry_time.txt-এ টাইমজোন-বিহীন টাইমস্ট্যাম্প রয়েছে। UTC হিসেবে ধরে নেওয়া হচ্ছে।",
        "warning_removed_existing_outputs": "सतर्कता: সম্পূর্ণ পুনরুৎপাদনের আগে {}টি বিদ্যমান আউটপুট ফাইল মুছে ফেলা হয়েছে।",
    },
    "de": {
        "error_lang_detection": "Fehler bei der Erkennung der Systemsprache: {}",
        "file_not_found": "Fehler: Datei nicht gefunden: {}",
        "json_decode_error": "JSON-Decodierungsfehler: {}",
        "start_processing": "🚀 Verarbeitung gestartet: Lade {}...",
        "extracted_entries": "{0} Einträge extrahiert, davon sind {1} Gemini-Verlauf.",
        "converting_markdown": "Konvertiere zu Markdown...",
        "appended_to_file": "Chatverläufe an Datei angehängt: {}",
        "written_to_file": "Chatverläufe in Datei geschrieben: {}",
        "processing_complete": "✅ Abgeschlossen: Verlauf von {0} bis {1} in insgesamt {2} Dateien gespeichert.",
        "error_occurred": "Ein Fehler ist aufgetreten: {}",
        "warning_last_entry_time_empty": "Warnung: last_entry_time.txt ist leer. Wechsel in den Modus zur vollständigen Regenerierung.",
        "warning_last_entry_time_invalid": "Warnung: Ungültiger Zeitstempel in last_entry_time.txt ({!r}). Wechsel in den Modus zur vollständigen Regenerierung.",
        "warning_last_entry_time_naive": "Warnung: last_entry_time.txt enthält einen Zeitstempel ohne Zeitzone. UTC wird angenommen.",
        "warning_removed_existing_outputs": "Warnung: {} vorhandene Ausgabedatei(en) vor der vollständigen Regenerierung entfernt.",
    },
    "en": {
        "error_lang_detection": "Error while detecting system language: {}",
        "file_not_found": "Error: File not found: {}",
        "json_decode_error": "JSON decode error: {}",
        "start_processing": "🚀 Starting processing: Loading {}...",
        "extracted_entries": "Extracted {0} entries, of which {1} are Gemini history.",
        "converting_markdown": "Converting to Markdown...",
        "appended_to_file": "Chat histories appended to file: {}",
        "written_to_file": "Chat histories written to file: {}",
        "processing_complete": "✅ Completed: Saved history after {0} to {1} into a total of {2} files.",
        "error_occurred": "An error occurred: {}",
        "warning_last_entry_time_empty": "Warning: last_entry_time.txt is empty. Switching to full regeneration mode.",
        "warning_last_entry_time_invalid": "Warning: Invalid timestamp in last_entry_time.txt ({!r}). Switching to full regeneration mode.",
        "warning_last_entry_time_naive": "Warning: last_entry_time.txt has a timezone-naive timestamp. Assuming UTC.",
        "warning_removed_existing_outputs": "Warning: Removed {} existing output file(s) before full regeneration.",
    },
    "es": {
        "error_lang_detection": "Error al detectar el idioma del sistema: {}",
        "file_not_found": "Error: Archivo no encontrado: {}",
        "json_decode_error": "Error al decodificar JSON: {}",
        "start_processing": "🚀 Iniciando procesamiento: Cargando {}...",
        "extracted_entries": "Se extrajeron {0} entradas, de las cuales {1} son historial de Gemini.",
        "converting_markdown": "Convirtiendo a Markdown...",
        "appended_to_file": "Historiales de chat agregados al archivo: {}",
        "written_to_file": "Historiales de chat escritos en el archivo: {}",
        "processing_complete": "✅ Completado: Historial guardado desde {0} hasta {1} en un total de {2} archivos.",
        "error_occurred": "Ocurrió un error: {}",
        "warning_last_entry_time_empty": "Advertencia: last_entry_time.txt está vacío. Cambiando al modo de regeneración completa.",
        "warning_last_entry_time_invalid": "Advertencia: Marca de tiempo inválida en last_entry_time.txt ({!r}). Cambiando al modo de regeneración completa.",
        "warning_last_entry_time_naive": "Advertencia: last_entry_time.txt tiene una marca de tiempo sin zona horaria. Se asume UTC.",
        "warning_removed_existing_outputs": "Advertencia: Se eliminaron {} archivos de salida existentes antes de la regeneración completa.",
    },
    "fa": {
        "error_lang_detection": "خطا در شناسایی زبان سیستم: {}",
        "file_not_found": "خطا: فایل پیدا نشد: {}",
        "json_decode_error": "خطای رمزگشایی JSON: {}",
        "start_processing": "🚀 شروع پردازش: در حال بارگذاری {}...",
        "extracted_entries": "{0} ورودی استخراج شد که {1} مورد از آن‌ها تاریخچه Gemini است.",
        "converting_markdown": "در حال تبدیل به Markdown...",
        "appended_to_file": "تاریخچه چت به فایل اضافه شد: {}",
        "written_to_file": "تاریخچه چت در فایل نوشته شد: {}",
        "processing_complete": "✅ تکمیل شد: تاریخچه از {0} تا {1} در مجموع در {2} فایل ذخیره شد.",
        "error_occurred": "یک خطا رخ داد: {}",
        "warning_last_entry_time_empty": "هشدار: فایل last_entry_time.txt خالی است. تغییر به حالت بازسازی کامل.",
        "warning_last_entry_time_invalid": "هشدار: برچسب زمان در last_entry_time.txt نامعتبر است ({!r}). تغییر به حالت بازسازی کامل.",
        "warning_last_entry_time_naive": "هشدار: برچسب زمان در last_entry_time.txt فاقد اطلاعات منطقه زمانی است. بر پایه UTC فرض می‌شود.",
        "warning_removed_existing_outputs": "هشدار: پاکسازی {} فایل خروجی موجود پیش از بازسازی کامل انجام شد.",
    },
    "fr": {
        "error_lang_detection": "Erreur lors de la détection de la langue du système : {}",
        "file_not_found": "Erreur : Fichier non trouvé : {}",
        "json_decode_error": "Erreur de décodage JSON : {}",
        "start_processing": "🚀 Démarrage du traitement : Chargement de {}...",
        "extracted_entries": "{0} entrées extraites, dont {1} sont l'historique Gemini.",
        "converting_markdown": "Conversion en Markdown...",
        "appended_to_file": "Historiques de chat ajoutés au fichier : {}",
        "written_to_file": "Historiques de chat écrits dans le fichier : {}",
        "processing_complete": "✅ Terminé : Historique sauvegardé de {0} à {1} dans un total de {2} fichiers.",
        "error_occurred": "Une erreur est survenue : {}",
        "warning_last_entry_time_empty": "Avertissement : last_entry_time.txt est vide. Passage en mode de régénération complète.",
        "warning_last_entry_time_invalid": "Avertissement : Horodatage non valide dans last_entry_time.txt ({!r}). Passage en mode de régénération complète.",
        "warning_last_entry_time_naive": "Avertissement : last_entry_time.txt contient un horodatage sans fuseau horaire. UTC sera supposé.",
        "warning_removed_existing_outputs": "Avertissement : {} fichier(s) de sortie existant(s) supprimé(s) avant la régénération complète.",
    },
    "hi": {
        "error_lang_detection": "त्रुटि: सिस्टम भाषा का पता लगाने में समस्या: {}",
        "file_not_found": "त्रुटि: फ़ाइल सापडली नाही: {}",
        "json_decode_error": "JSON डिकोड त्रुटी: {}",
        "start_processing": "🚀 प्रसंस्करण शुरू हो रहा है: {} लोड हो रहा है...",
        "extracted_entries": "{0} प्रविष्टियाँ निकाली गईं, जिनमें से {1} Gemini इतिहास हैं।",
        "converting_markdown": "Markdown में परिवर्तित हो रहा है...",
        "appended_to_file": "चैट इतिहास फ़ाइल में जोड़ा गया: {}",
        "written_to_file": "चैट इतिहास फ़ाइल में लिखा गया: {}",
        "processing_complete": "✅ पूर्ण: {0} से {1} तक का इतिहास कुल {2} फ़ाइलों में सहेजा गया।",
        "error_occurred": "एक त्रुटी आली आहे: {}",
        "warning_last_entry_time_empty": "चेतावनी: last_entry_time.txt खाली है। पूर्ण पुनर्जनन (full regeneration) मोड पर स्विच किया जा रहा है।",
        "warning_last_entry_time_invalid": "चेतावनी: last_entry_time.txt में अमान्य टाइमस्टैम्प ({!r}) है। पूर्ण पुनर्जनन मोड पर स्विच किया जा रहा है।",
        "warning_last_entry_time_naive": "चेतावनी: last_entry_time.txt में टाइमज़ोन-रहित टाइमस्टैम्प है। इसे UTC माना जा रहा है।",
        "warning_removed_existing_outputs": "चेतावनी: पूर्ण पुनर्जनन से पहले {} मौजूदा आउटपुट फ़ाइलें हटा दी गई हैं।",
    },
    "id": {
        "error_lang_detection": "Error saat mendeteksi bahasa sistem: {}",
        "file_not_found": "Error: File tidak ditemukan: {}",
        "json_decode_error": "Error decode JSON: {}",
        "start_processing": "🚀 Memulai pemrosesan: Memuat {}...",
        "extracted_entries": "Diekstrak {0} entri, di antaranya {1} adalah riwayat Gemini.",
        "converting_markdown": "Mengonversi ke Markdown...",
        "appended_to_file": "Riwayat obrolan ditambahkan ke file: {}",
        "written_to_file": "Riwayat obrolan ditulis ke file: {}",
        "processing_complete": "✅ Selesai: Riwayat disimpan dari {0} hingga {1} dalam total {2} file.",
        "error_occurred": "Terjadi kesalahan: {}",
        "warning_last_entry_time_empty": "Peringatan: last_entry_time.txt kosong. Beralih ke mode regenerasi penuh.",
        "warning_last_entry_time_invalid": "Peringatan: Timestamp tidak valid di last_entry_time.txt ({!r}). Beralih ke mode regenerasi penuh.",
        "warning_last_entry_time_naive": "Peringatan: last_entry_time.txt memiliki timestamp tanpa informasi zona waktu. Diasumsikan sebagai UTC.",
        "warning_removed_existing_outputs": "Peringatan: Menghapus {} file output yang ada sebelum melakukan regenerasi penuh.",
    },
    "ja": {
        "error_lang_detection": "システム言語の検出中にエラーが発生しました: {}",
        "file_not_found": "エラー: ファイルが見つかりません: {}",
        "json_decode_error": "JSONデコードエラー: {}",
        "start_processing": "🚀 処理開始: {} を読み込み中...",
        "extracted_entries": "{0} 件抽出され、うち Gemini の履歴は {1} 件ありました。",
        "converting_markdown": "Markdown に変換中...",
        "appended_to_file": "チャット履歴をファイルに追記しました: {}",
        "written_to_file": "チャット履歴をファイルに書き込みました: {}",
        "processing_complete": "✅ 完了しました: {0} より後の {1} までの履歴を延べ {2} ファイルに分割保存しました。",
        "error_occurred": "エラーが発生しました: {}",
        "warning_last_entry_time_empty": "警告: last_entry_time.txt が空です。全件再生成モードに切り替えます。",
        "warning_last_entry_time_invalid": "警告: last_entry_time.txt のタイムスタンプが不正です（{!r}）。全件再生成モードに切り替えます。",
        "warning_last_entry_time_naive": "警告: last_entry_time.txt のタイムスタンプにタイムゾーン情報がありません。UTC として扱います。",
        "warning_removed_existing_outputs": "警告: 全件再生成の前に既存の出力ファイル {} 件を削除しました。",
    },
    "jv": {
        "error_lang_detection": "Kesalahan saat mendeteksi bahasa sistem: {}",
        "file_not_found": "Kesalahan: Berkas tidak ditemukan: {}",
        "json_decode_error": "Kesalahan dekode JSON: {}",
        "start_processing": "🚀 Memulai pemrosesan: Memuat {}...",
        "extracted_entries": "Ditemukan {0} entri, di mana {1} adalah riwayat Gemini.",
        "converting_markdown": "Mengonversi ke Markdown...",
        "appended_to_file": "Riwayat obrolan ditambahkan ke berkas: {}",
        "written_to_file": "Riwayat obrolan ditulis ke berkas: {}",
        "processing_complete": "✅ Selesai: Riwayat disimpan dari {0} hingga {1} dalam total {2} berkas.",
        "error_occurred": "Terjadi kesalahan: {}",
        "warning_last_entry_time_empty": "Pèngetan: last_entry_time.txt kothong. Ngalih menyang mode regenerasi lengkap.",
        "warning_last_entry_time_invalid": "Pèngetan: Timestamp ora sah ing last_entry_time.txt ({!r}). Ngalih menyang mode regenerasi lengkap.",
        "warning_last_entry_time_naive": "Pèngetan: last_entry_time.txt nduweni timestamp tanpa zona wektu. Dianggep minangka UTC.",
        "warning_removed_existing_outputs": "Pèngetan: Busak {} berkas output sing wis ana sadurunge regenerasi lengkap.",
    },
    "ko": {
        "error_lang_detection": "시스템 언어 설정 감지 중 오류 발생: {}",
        "file_not_found": "오류: 파일을 찾을 수 없습니다: {}",
        "json_decode_error": "JSON 디코드 오류: {}",
        "start_processing": "🚀 처리 시작: {} 로드 중...",
        "extracted_entries": "{0}개의 항목이 추출되었으며, 그 중 {1}개는 Gemini 기록입니다.",
        "converting_markdown": "Markdown으로 변환 중...",
        "appended_to_file": "채팅 기록이 파일에 추가되었습니다: {}",
        "written_to_file": "채팅 기록이 파일에 작성되었습니다: {}",
        "processing_complete": "✅ 완료: {0}부터 {1}까지의 기록이 총 {2}개의 파일에 저장되었습니다.",
        "error_occurred": "오류가 발생했습니다: {}",
        "warning_last_entry_time_empty": "경고: last_entry_time.txt 파일이 비어 있습니다. 전체 재생성 모드로 전환합니다.",
        "warning_last_entry_time_invalid": "경고: last_entry_time.txt의 타임스탬프가 올바르지 않습니다 ({!r}). 전체 재생성 모드로 전환합니다.",
        "warning_last_entry_time_naive": "경고: last_entry_time.txt에 시간대(timezone) 정보가 없는 타임스탬프가 포함되어 있습니다. UTC로 간주합니다.",
        "warning_removed_existing_outputs": "경고: 전체 재생성 전에 기존 출력 파일 {}개를 삭제했습니다.",
    },
    "mr": {
        "error_lang_detection": "त्रुटी: सिस्टम भाषा ओळखण्यात समस्या: {}",
        "file_not_found": "त्रुटी: फाइल सापडली नाही: {}",
        "json_decode_error": "JSON डिकोड त्रुटी: {}",
        "start_processing": "🚀 प्रक्रिया सुरू होणार आहे: {} लोड होत आहे...",
        "extracted_entries": "{0} नोंदी काढल्या, ज्यापैकी {1} Gemini इतिहास आहे.",
        "converting_markdown": "Markdown मध्ये रूपांतरित करत आहे...",
        "appended_to_file": "चॅट इतिहास फाइलमध्ये जोडला गेला: {}",
        "written_to_file": "चॅट इतिहास फाइलमध्ये लिहिला गेला: {}",
        "processing_complete": "✅ पूर्ण झाले: इतिहास {0} पासून {1} पर्यंत एकूण {2} फाइलांमध्ये जतन केला गेला.",
        "error_occurred": "एक त्रुटी आली आहे: {}",
        "warning_last_entry_time_empty": "तंबी: last_entry_time.txt रिकामी आहे. पूर्ण पुनरुत्पादन (full regeneration) मोडवर स्विच करत आहे.",
        "warning_last_entry_time_invalid": "तंबी: last_entry_time.txt मध्ये अवैध टाइमस्टँप ({!r}) आहे. पूर्ण पुनरुत्पादन मोडवर स्विच करत आहे.",
        "warning_last_entry_time_naive": "तंबी: last_entry_time.txt मध्ये टाइमझोन-विरहित टाइमस्टँप आहे. UTC मानले जात आहे.",
        "warning_removed_existing_outputs": "तंबी: पूर्ण पुनरुत्पादनापूर्वी {} विद्यमान आउटपुट फाइल्स हटवल्या गेल्या आहेत.",
    },
    "ms": {
        "error_lang_detection": "Ralat semasa mengesan bahasa sistem: {}",
        "file_not_found": "Ralat: Fail tidak dijumpai: {}",
        "json_decode_error": "Ralat nyahkod JSON: {}",
        "start_processing": "🚀 Memulakan pemprosesan: Memuat {}...",
        "extracted_entries": "Diekstrak {0} entri, di mana {1} adalah sejarah Gemini.",
        "converting_markdown": "Menukar kepada Markdown...",
        "appended_to_file": "Sejarah sembang ditambah ke fail: {}",
        "written_to_file": "Sejarah sembang ditulis ke fail: {}",
        "processing_complete": "✅ Selesai: Sejarah disimpan dari {0} hingga {1} dalam jumlah {2} fail.",
        "error_occurred": "Ralat telah berlaku: {}",
        "warning_last_entry_time_empty": "Amaran: last_entry_time.txt adalah kosong. Beralih ke mod regenerasi penuh.",
        "warning_last_entry_time_invalid": "Amaran: Penanda masa tidak sah dalam last_entry_time.txt ({!r}). Beralih ke mod regenerasi penuh.",
        "warning_last_entry_time_naive": "Amaran: last_entry_time.txt mempunyai penanda masa tanpa zon masa. Mengandalkan UTC.",
        "warning_removed_existing_outputs": "Amaran: Mengeluarkan {} fail output sedia ada sebelum regenerasi penuh.",
    },
    "pa": {
        "error_lang_detection": "ਸਿਸਟਮ ਭਾਸ਼ਾ ਦਾ ਪਤਾ ਲਗਾਉਂਦੇ ਸਮੇਂ ਤਰੁੱਟੀ: {}",
        "file_not_found": "ਤਰੁੱਟੀ: ਫਾਈਲ ਨਹੀਂ ਮਿਲੀ: {}",
        "json_decode_error": "JSON ਡੀਕੋਡ ਤਰੁੱਟੀ: {}",
        "start_processing": "🚀 ਪ੍ਰਕਿਰਿਆ ਸ਼ੁਰੂ ਹੋ ਰਹੀ ਹੈ: {} ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...",
        "extracted_entries": "{0} ਐਂਟਰੀਆਂ ਨਿਕਾਲੀਆਂ ਗਈਆਂ, ਜਿਨ੍ਹਾਂ ਵਿੱਚੋਂ {1} Gemini ਇਤਿਹਾਸ ਹੈ।",
        "converting_markdown": "Markdown ਵਿੱਚ ਬਦਲ ਰਿਹਾ ਹੈ...",
        "appended_to_file": "ਚੈਟ ਇਤਿਹਾਸ ਫਾਈਲ ਵਿੱਚ ਸ਼ਾਮਲ ਕੀਤਾ ਗਿਆ: {}",
        "written_to_file": "ਚੈਟ ਇਤਿਹਾਸ ਫਾਈਲ ਵਿੱਚ ਲਿਖਿਆ ਗਿਆ: {}",
        "processing_complete": "✅ ਮੁਕੰਮਲ: ਇਤਿਹਾਸ {0} ਤੋਂ {1} ਤੱਕ ਕੁੱਲ {2} ਫਾਈਲਾਂ ਵਿੱਚ ਸੁਰੱਖਿਅਤ ਕੀਤਾ ਗਿਆ।",
        "error_occurred": "ਇੱਕ ਤਰੁੱਟੀ ਆਈ: {}",
        "warning_last_entry_time_empty": "ਚੇਤਾਵਨੀ: last_entry_time.txt ਖਾਲੀ ਹੈ। ਪੂਰੀ ਰੀਜਨਰੇਸ਼ਨ (full regeneration) ਮੋਡ 'ਤੇ ਸਵਿਚ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ।",
        "warning_last_entry_time_invalid": "ਚੇਤਾਵਨੀ: last_entry_time.txt ਵਿੱਚ ਅਵੈਧ ਟਾਈਮਸਟੈਂਪ ({!r}) ਹੈ। ਪੂਰੀ ਰੀਜਨਰੇਸ਼ਨ ਮੋਡ 'ਤੇ ਸਵਿਚ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ।",
        "warning_last_entry_time_naive": "ਚੇਤਾਵਨੀ: last_entry_time.txt ਵਿੱਚ ਟਾਈਮਜ਼ੋਨ-ਰਹਿਤ ਟਾਈਮਸਟੈਂਪ ਹੈ। ਇਸਨੂੰ UTC ਮੰਨਿਆ ਜਾ ਰਿਹਾ ਹੈ।",
        "warning_removed_existing_outputs": "ਚੇਤਾਵਨੀ: ਪੂਰੀ ਰੀਜਨਰੇਸ਼ਨ ਤੋਂ ਪਹਿਲਾਂ {} ਮੌਜੂਦਾ ਆਉਟਪੁੱਟ ਫਾਈਲਾਂ ਨੂੰ ਹਟਾ ਦਿੱਤਾ ਗਿਆ ਹੈ।",
    },
    "pt": {
        "error_lang_detection": "Erro ao detectar o idioma do sistema: {}",
        "file_not_found": "Erro: Arquivo não encontrado: {}",
        "json_decode_error": "Erro de decodificação JSON: {}",
        "start_processing": "🚀 Iniciando processamento: Carregando {}...",
        "extracted_entries": "Extraídas {0} entradas, das quais {1} são histórico do Gemini.",
        "converting_markdown": "Convertendo para Markdown...",
        "appended_to_file": "Históricos de chat adicionados ao arquivo: {}",
        "written_to_file": "Históricos de chat escritos no arquivo: {}",
        "processing_complete": "✅ Concluído: Histórico salvo de {0} a {1} em um total de {2} arquivos.",
        "error_occurred": "Ocorreu um erro: {}",
        "warning_last_entry_time_empty": "Aviso: last_entry_time.txt está vazio. Alternando para o modo de regeneração completa.",
        "warning_last_entry_time_invalid": "Aviso: Carimbo de data/hora inválido em last_entry_time.txt ({!r}). Alternando para o modo de regeneração completa.",
        "warning_last_entry_time_naive": "Aviso: last_entry_time.txt possui um carimbo de data/hora sem fuso horário. Assumindo UTC.",
        "warning_removed_existing_outputs": "Aviso: Removido(s) {} arquivo(s) de saída existente(s) antes da regeneración completa.",
    },
    "ru": {
        "error_lang_detection": "Ошибка при определении языка системы: {}",
        "file_not_found": "Ошибка: Файл не найден: {}",
        "json_decode_error": "Ошибка декодирования JSON: {}",
        "start_processing": "🚀 Начало обработки: Загрузка {}...",
        "extracted_entries": "Извлечено {0} записей, из которых {1} относятся к истории Gemini.",
        "converting_markdown": "Преобразование в Markdown...",
        "appended_to_file": "История чата добавлена в файл: {}",
        "written_to_file": "История чата записана в файл: {}",
        "processing_complete": "✅ Завершено: История сохранена с {0} по {1} в общей сложности в {2} файлах.",
        "error_occurred": "Произошла ошибка: {}",
        "warning_last_entry_time_empty": "Предупреждение: Файл last_entry_time.txt пуст. Переключение в режим полной регенерации.",
        "warning_last_entry_time_invalid": "Предупреждение: Некорректная метка времени в last_entry_time.txt ({!r}). Переключение в режим полной регенерации.",
        "warning_last_entry_time_naive": "Предупреждение: Метка времени в last_entry_time.txt не содержит указания часового пояса. Предполагается UTC.",
        "warning_removed_existing_outputs": "Предупреждение: Удалено {} существующих выходных файлов перед полной регенерацией.",
    },
    "sw": {
        "error_lang_detection": "Hitilafu wakati wa kugundua lugha ya mfumo: {}",
        "file_not_found": "Hitilafu: Faili haikupatikana: {}",
        "json_decode_error": "Hitilafu ya kutafsiri JSON: {}",
        "start_processing": "🚀 Kuanzia usindikaji: Inapakia {}...",
        "extracted_entries": "Imechota rekodi {0}, ambapo {1} ni historia ya Gemini.",
        "converting_markdown": "Inabadilisha kuwa Markdown...",
        "appended_to_file": "Historia za mazungumzo zimeongezwa kwenye faili: {}",
        "written_to_file": "Historia za mazungumzo zimeandikwa kwenye faili: {}",
        "processing_complete": "✅ Imekamilika: Historia imehifadhiwa kutoka {0} hadi {1} katika jumla ya faili {2}.",
        "error_occurred": "Hitilafu imetokea: {}",
        "warning_last_entry_time_empty": "Onyo: last_entry_time.txt ni tupu. Inabadilisha kwenda hali ya uzalishaji upya kikamilifu.",
        "warning_last_entry_time_invalid": "Onyo: Alama ya muda si halali katika last_entry_time.txt ({!r}). Inabadilisha kwenda hali ya uzalishaji upya kikamilifu.",
        "warning_last_entry_time_naive": "Onyo: last_entry_time.txt ina alama ya muda isiyo na eneo la muda. Inachukuliwa kama UTC.",
        "warning_removed_existing_outputs": "Onyo: Faili {} zilizopo za matokeo zimeondolewa kabla ya uzalishaji upya kikamilifu.",
    },
    "ta": {
        "error_lang_detection": "சிஸ்டம் மொழியை கண்டறிதலில் பிழை: {}",
        "file_not_found": "பிழை: கோப்பு காணப்படவில்லை: {}",
        "json_decode_error": "JSON குறியாக்க பிழை: {}",
        "start_processing": "🚀 செயலாக்கம் தொடங்குகிறது: {} ஏற்றப்படுகிறது...",
        "extracted_entries": "{0} உள்ளீடுகள் பிரித்தெடுக்கப்பட்டன, அவற்றில் {1} Gemini வரலாறு.",
        "converting_markdown": "Markdown ஆக மாற்றுகிறது...",
        "appended_to_file": "அரட்டை வரலாறு கோப்பில் இணைக்கப்பட்டது: {}",
        "written_to_file": "அரட்டை வரலாறு கோப்பில் எழுதப்பட்டது: {}",
        "processing_complete": "✅ முடிந்தது: {0} முதல் {1} வரையிலான வரலாறு மொத்தம் {2} கோப்புகளில் சேமிக்கப்பட்டது.",
        "error_occurred": "ஒரு பிழை ஏற்பட்டது: {}",
        "warning_last_entry_time_empty": "எச்சரிக்கை: last_entry_time.txt காலியாக உள்ளது. முழுமையான மறுஉருவாக்க பயன்முறைக்கு மாறுகிறது.",
        "warning_last_entry_time_invalid": "எச்சரிக்கை: last_entry_time.txt இல் தவறான நேரமுத்திரை ({!r}). முழுமையான மறுஉருவாக்க பயன்முறைக்கு மாறுகிறது.",
        "warning_last_entry_time_naive": "எச்சரிக்கை: last_entry_time.txt இல் உள்ள நேரமுத்திரையில் நேரமண்டல தகவல் இல்லை. UTC எனக் கருதப்படுகிறது.",
        "warning_removed_existing_outputs": "எச்சரிக்கை: முழுமையான மறுஉருவாக்கத்திற்கு முன் ஏற்கனவே உள்ள நாடுகளில் உள்ள {} வெளியீட்டுக் கோப்புகள் நீக்கப்பட்டன.",
    },
    "te": {
        "error_lang_detection": "సిస్టమ్ భాషను గుర్తించడంలో లోపం: {}",
        "file_not_found": "లోపం: ఫైల్ కనుగొనబడలేదు: {}",
        "json_decode_error": "JSON డీకోడ్ లోపం: {}",
        "start_processing": "🚀 ప్రాసెసింగ్ ప్రారంభం: {} లోడ్ అవుతోంది...",
        "extracted_entries": "{0} ఎంట్రీలు తీసుకోబడ్డాయి, వాటిలో {1} జెమినీ చరిత్ర.",
        "converting_markdown": "Markdown కు మార్చడం...",
        "appended_to_file": "చాట్ చరిత్ర ఫైల్‌కు జోడించబడింది: {}",
        "written_to_file": "చాట్ చరిత్ర ఫైల్‌కు రాయబడింది: {}",
        "processing_complete": "✅ పూర్తయింది: చరిత్ర {0} నుండి {1} వరకు మొత్తం {2} ఫైళ్లలో సేవ్ చేయబడింది.",
        "error_occurred": "లోపం సంభవించింది: {}",
        "warning_last_entry_time_empty": "హెచ్చరిక: last_entry_time.txt ఖాళీగా ఉంది. పూర్తి పునరుత్పత్తి (full regeneration) మోడ్‌కు మారుతోంది.",
        "warning_last_entry_time_invalid": "హెచ్చరిక: last_entry_time.txt లో చెల్లని టైమ్‌స్టాంప్ ({!r}) ఉంది. పూర్తి పునరుత్పత్తి మోడ్‌కు మారుతోంది.",
        "warning_last_entry_time_naive": "హెచ్చరిక: last_entry_time.txt లోని టైమ్‌స్టాంప్‌కు టైమ్‌జోన్ సమాచారం లేదు. UTC గా భావించబడుతుంది.",
        "warning_removed_existing_outputs": "హెచ్చరిక: పూర్తి పునరుత్పత్తికి ముందు ఇప్పటికే ఉన్న {} అవుట్‌పుట్ ఫైల్‌లు తీసివేయబడ్డాయి.",
    },
    "th": {
        "error_lang_detection": "เกิดข้อผิดพลาดขณะตรวจจับภาษาระบบ: {}",
        "file_not_found": "ข้อผิดพลาด: ไม่พบไฟล์: {}",
        "json_decode_error": "ข้อผิดพลาดในการถอดรหัส JSON: {}",
        "start_processing": "🚀 เริ่มการประมวลผล: กำลังโหลด {}...",
        "extracted_entries": "ดึงข้อมูล {0} รายการ ซึ่งมีประวัติของ Gemini จำนวน {1} รายการ",
        "converting_markdown": "กำลังแปลงเป็น Markdown...",
        "appended_to_file": "ประวัติการแชทถูกเพิ่มลงในไฟล์: {}",
        "written_to_file": "ประวัติการแชทถูกเขียนลงในไฟล์: {}",
        "processing_complete": "✅ เสร็จสิ้น: บันทึกประวัติจาก {0} ถึง {1} ลงในไฟล์ทั้งหมด {2} ไฟล์",
        "error_occurred": "เกิดข้อผิดพลาด: {}",
        "warning_last_entry_time_empty": "คำเตือน: ไฟล์ last_entry_time.txt ว่างเปล่า กำลังเปลี่ยนเป็นโหมดสร้างใหม่ทั้งหมด",
        "warning_last_entry_time_invalid": "คำเตือน: การประทับเวลาใน last_entry_time.txt ไม่ถูกต้อง ({!r}) กำลังเปลี่ยนเป็นโหมดสร้างใหม่ทั้งหมด",
        "warning_last_entry_time_naive": "คำเตือน: การประทับเวลาใน last_entry_time.txt ไม่มีข้อมูลเขตเวลา จะถือว่าเป็นเวลา UTC",
        "warning_removed_existing_outputs": "คำเตือน: ลบไฟล์เอาต์พุตที่มีอยู่เดิมจำนวน {} ไฟล์ ก่อนเริ่มการสร้างใหม่ทั้งหมด",
    },
    "tr": {
        "error_lang_detection": "Sistem dili algılanırken hata oluştu: {}",
        "file_not_found": "Hata: Dosya bulunamadı: {}",
        "json_decode_error": "JSON kod çözme hatası: {}",
        "start_processing": "🚀 İşleme başlıyor: {} yükleniyor...",
        "extracted_entries": "{0} giriş çıkarıldı, bunların {1} tanesi Gemini geçmişi.",
        "converting_markdown": "Markdown'a dönüştürülüyor...",
        "appended_to_file": "Sohbet geçmişi dosyaya eklendi: {}",
        "written_to_file": "Sohbet geçmişi dosyaya yazıldı: {}",
        "processing_complete": "✅ Tamamlandı: {0} ile {1} arasındaki geçmiş toplam {2} dosyaya kaydedildi.",
        "error_occurred": "Bir hata oluştu: {}",
        "warning_last_entry_time_empty": "Uyarı: last_entry_time.txt boş. Tam adımlı yeniden oluşturma moduna geçiliyor.",
        "warning_last_entry_time_invalid": "Uyarı: last_entry_time.txt dosyasındaki zaman damgası geçersiz ({!r}). Tam adımlı yeniden oluşturma moduna geçiliyor.",
        "warning_last_entry_time_naive": "Uyarı: last_entry_time.txt dosyasındaki zaman damgası saat dilimi bilgisi içermiyor. UTC olduğu varsayılıyor.",
        "warning_removed_existing_outputs": "Uyarı: Tam adımlı yeniden oluşturma öncesinde mevcut {} çıktı dosyası silindi.",
    },
    "uk": {
        "error_lang_detection": "Помилка під час визначення мови системи: {}",
        "file_not_found": "Помилка: Файл не знайдено: {}",
        "json_decode_error": "Помилка декодування JSON: {}",
        "start_processing": "🚀 Початок обробки: Завантаження {}...",
        "extracted_entries": "Вилучено {0} записів, з яких {1} стосуються історії Gemini.",
        "converting_markdown": "Конвертація в Markdown...",
        "appended_to_file": "Історія чату додана до файлу: {}",
        "written_to_file": "Історія чату записана у файл: {}",
        "processing_complete": "✅ Завершено: Історія з {0} по {1} збережена усього в {2} файлах.",
        "error_occurred": "Сталася помилка: {}",
        "warning_last_entry_time_empty": "Попередження: Файл last_entry_time.txt порожній. Переключення в режим повної регенерації.",
        "warning_last_entry_time_invalid": "Попередження: Некоректна мітка часу в last_entry_time.txt ({!r}). Переключення в режим повної регенерації.",
        "warning_last_entry_time_naive": "Попередження: Мітка часу в last_entry_time.txt не містить інформації про часовий пояс. Припускається UTC.",
        "warning_removed_existing_outputs": "Попередження: Видалено {} існуючих вихідних файлів перед повною регенерацією.",
    },
    "ur": {
        "error_lang_detection": "سسٹم زبان کا پتہ لگانے में خرابی: {}",
        "file_not_found": "خرابی: فائل نہیں ملی: {}",
        "json_decode_error": "JSON ڈی کوڈنگ کی خرابی: {}",
        "start_processing": "🚀 پراسیسنگ شروع ہو رہی ہے: {} لوڈ ہو رہا ہے...",
        "extracted_entries": "{0} اندراجات نکالے گئے، جن میں سے {1} Gemini کی تاریخ ہے۔",
        "converting_markdown": "Markdown میں تبدیل کیا جا رہا ہے...",
        "appended_to_file": "چیٹ کی تاریخ فائل میں شامل کر دی گئی ہے: {}",
        "written_to_file": "چیٹ کی تاریخ فائل میں لکھ دی گئی ہے: {}",
        "processing_complete": "✅ مکمل ہو گیا: تاریخ {0} سے {1} تک کل {2} فائلوں میں محفوظ کر دی گئی ہے۔",
        "error_occurred": "ایک خرابی پیش آئی: {}",
        "warning_last_entry_time_empty": "انتباہ: last_entry_time.txt خالی ہے۔ مکمل بحالی (full regeneration) کے موڈ پر منتقل کیا جا رہا ہے۔",
        "warning_last_entry_time_invalid": "انتباہ: last_entry_time.txt میں غلط ٹائم اسٹیمپ ہے ({!r})۔ مکمل بحالی کے موڈ پر منتقل کیا جا رہا ہے۔",
        "warning_last_entry_time_naive": "انتباہ: last_entry_time.txt میں ٹائم زون کے بغیر ٹائم اسٹیمپ ہے۔ اسے UTC فرض کیا جا رہا ہے۔",
        "warning_removed_existing_outputs": "انتباہ: مکمل بحالی سے پہلے موصوفہ {} آؤٹ پٹ فائلیں ہٹا دی گئی ہیں۔",
    },
    "vi": {
        "error_lang_detection": "Lỗi khi phát hiện ngôn ngữ hệ thống: {}",
        "file_not_found": "Lỗi: Không tìm thấy tệp: {}",
        "json_decode_error": "Lỗi giải mã JSON: {}",
        "start_processing": "🚀 Bắt đầu xử lý: Đang tải {}...",
        "extracted_entries": "Đã trích xuất {0} mục, trong đó có {1} là lịch sử Gemini.",
        "converting_markdown": "Đang chuyển đổi sang Markdown...",
        "appended_to_file": "Lịch sử trò chuyện đã được thêm vào tệp: {}",
        "written_to_file": "Lịch sử trò chuyện đã được ghi vào tệp: {}",
        "processing_complete": "✅ Hoàn thành: Đã lưu lịch sử từ {0} đến {1} vào tổng cộng {2} tệp.",
        "error_occurred": "Đã xảy ra lỗi: {}",
        "warning_last_entry_time_empty": "Cảnh báo: last_entry_time.txt trống. Chuyển sang chế độ tái tạo toàn bộ.",
        "warning_last_entry_time_invalid": "Cảnh báo: Dấu thời gian không hợp lệ trong last_entry_time.txt ({!r}). Chuyển sang chế độ tái tạo toàn bộ.",
        "warning_last_entry_time_naive": "Cảnh báo: last_entry_time.txt có dấu thời gian không chứa múi giờ. Giả định là UTC.",
        "warning_removed_existing_outputs": "Cảnh báo: Đã xóa {} tệp đầu ra hiện có trước khi tái tạo toàn bộ.",
    },
    "zh_CN": {
        "error_lang_detection": "检测系统语言时出错：{}",
        "file_not_found": "错误：未找到文件：{}",
        "json_decode_error": "JSON 解码错误：{}",
        "start_processing": "🚀 开始处理：正在加载 {}...",
        "extracted_entries": "提取了 {0} 条条目，其中 {1} 条是 Gemini 历史记录。",
        "converting_markdown": "正在转换为 Markdown...",
        "appended_to_file": "聊天历史已追加到文件：{}",
        "written_to_file": "聊天历史已写入文件：{}",
        "processing_complete": "✅ 完成：已将 {0} 到 {1} 之间的历史记录保存到共计 {2} 个文件中。",
        "error_occurred": "发生错误：{}",
        "warning_last_entry_time_empty": "警告：last_entry_time.txt 为空，已切换为全量重新生成模式。",
        "warning_last_entry_time_invalid": "警告：last_entry_time.txt 中的时间戳无效（{!r}），已切换为全量重新生成模式。",
        "warning_last_entry_time_naive": "警告：last_entry_time.txt 中的时间戳缺少时区信息，将按 UTC 处理。",
        "warning_removed_existing_outputs": "警告：已在全量重新生成前删除 {} 个既有输出文件。",
    },
    "zh_TW": {
        "error_lang_detection": "檢測系統語言時出錯：{}",
        "file_not_found": "錯誤：未找到文件：{}",
        "json_decode_error": "JSON 解碼錯誤：{}",
        "start_processing": "🚀 開始處理：正在加載 {}...",
        "extracted_entries": "提取了 {0} 條條目，其中 {1} 條是 Gemini 歷史記錄。",
        "converting_markdown": "正在轉換為 Markdown...",
        "appended_to_file": "聊天歷史已追加到文件：{}",
        "written_to_file": "聊天歷史已寫入文件：{}",
        "processing_complete": "✅ 完成：已將 {0} 到 {1} 之間的歷史記錄保存到共計 {2} 個文件中。",
        "error_occurred": "發生錯誤：{}",
        "warning_last_entry_time_empty": "警告：last_entry_time.txt 為空，已切換為全量重新產生模式。",
        "warning_last_entry_time_invalid": "警告：last_entry_time.txt 中的時間戳無效（{!r}），已切換為全量重新產生模式。",
        "warning_last_entry_time_naive": "警告：last_entry_time.txt 中的時間戳缺少時區資訊，將視為 UTC。",
        "warning_removed_existing_outputs": "警告：已在全量重新產生前刪除 {} 個既有輸出檔。",
    },
}

@functools.lru_cache(maxsize=1)
def resolve_language_from_raw_locale(raw_locale: str) -> str:
    """Resolve language code from a raw locale string."""
    if not raw_locale:
        return "en"

    normalized_locale = raw_locale.replace("-", "_")
    normalized_locale_lower = normalized_locale.lower()

    # Keep language + region/script for Chinese variants before reducing to language only.
    if normalized_locale_lower in {"zh_cn", "zh_hans", "chinese_china"}:
        return "zh_CN"
    if normalized_locale_lower in {"zh_tw", "zh_hant", "chinese_taiwan"}:
        return "zh_TW"

    if normalized_locale in TRANSLATIONS:
        return normalized_locale

    mapped = LANG_MAP.get(raw_locale) or LANG_MAP.get(normalized_locale)
    if mapped in TRANSLATIONS:
        return mapped

    lang_code = normalized_locale_lower.split("_")[0]
    if lang_code in TRANSLATIONS:
        return lang_code

    # Handle locale strings such as "English_United States".
    language_name = normalized_locale.split("_")[0]
    mapped_from_language_name = LANG_MAP.get(language_name)
    if mapped_from_language_name in TRANSLATIONS:
        return mapped_from_language_name

    return "en"


def translate_for_lang(lang: str, key: str, *args: Any) -> str:
    """Translate a key using an explicit language code."""
    msg_map: dict[str, str] = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    msg: str = msg_map.get(key, TRANSLATIONS["en"].get(key, key))

    if args:
        try:
            return msg.format(*args)
        except IndexError:
            # Safety measure in case the number of placeholders and variables do not match
            return msg
    return msg


@functools.lru_cache(maxsize=1)
def get_system_language() -> str:
    """detect OS language setting"""
    raw_locale = ""
    try:
        lang_tuple = locale.getlocale()
        raw_locale = (lang_tuple[0] or "").strip()
        return resolve_language_from_raw_locale(raw_locale)
    except Exception as e:
        detected_lang = resolve_language_from_raw_locale(raw_locale)
        print(translate_for_lang(detected_lang, "error_lang_detection", e), file=sys.stderr)
        return "en"


def t(key: str, *args: Any) -> str:
    """Translation function"""
    lang = get_system_language()
    return translate_for_lang(lang, key, *args)


def print_error(message: str) -> None:
    """Print error messages to stderr."""
    print(message, file=sys.stderr)


def print_warning(key: str, *args: Any) -> None:
    """Print warning messages to stderr via translation table."""
    print_error(t(key, *args))


def load_json(filepath: str) -> list[dict[str, Any]]:
    """Load a JSON file"""
    if not os.path.exists(filepath):
        print_error(t("file_not_found", filepath))
        return []

    with open(filepath, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print_error(t("json_decode_error", e))
            return []


def load_last_entry_time(filepath: str) -> tuple[datetime, bool]:
    """Load last entry timestamp and decide whether full regeneration is required."""
    default_time = datetime.min.replace(tzinfo=timezone.utc)
    if not os.path.exists(filepath):
        return default_time, False

    with open(filepath, encoding="utf-8") as f:
        raw_time = f.read().strip()

    if not raw_time:
        print_warning("warning_last_entry_time_empty")
        return default_time, True

    try:
        parsed_time = datetime.fromisoformat(raw_time)
    except ValueError:
        print_warning("warning_last_entry_time_invalid", raw_time)
        return default_time, True

    if parsed_time.tzinfo is None:
        print_warning("warning_last_entry_time_naive")
        parsed_time = parsed_time.replace(tzinfo=timezone.utc)

    return parsed_time, False


def remove_numbered_output_files(base_name: str, ext: str) -> int:
    """Remove previously generated numbered output files and return count."""
    removed = 0
    base_leaf = os.path.basename(base_name)
    pattern = re.compile(rf"^{re.escape(base_leaf)}-\d{{2}}{re.escape(ext)}$")

    for entry in os.listdir(os.path.dirname(base_name) or "."):
        if not pattern.match(entry):
            continue
        file_path = os.path.join(os.path.dirname(base_name), entry) if os.path.dirname(base_name) else entry
        os.remove(file_path)
        removed += 1

    return removed


def decode_unicode_escapes(s: str) -> str:
    """Decode Unicode escape sequences"""

    def repl(match):
        return chr(int(match.group(1), 16))

    return re.sub(r"\\u([0-9a-fA-F]{4})", repl, s)


def html_to_markdown(html_str: str) -> str:
    """
    Simple HTML -> Markdown/Text conversion
    Remove HTML tags and format into readable text
    """
    if not html_str:
        return ""

    text = decode_unicode_escapes(html_str)
    text = html_module.unescape(text)

    # Replace major tags (h1-h6, li, p, div, br, b, strong) with Markdown-like symbols and line breaks
    # Headings (h1-h6) -> **Heading** + line break
    text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n**\1**\n", text, flags=re.IGNORECASE)

    # List items (li) -> - + line break
    text = re.sub(r"<li[^>]*>", r"\n- ", text, flags=re.IGNORECASE)

    # Paragraphs (p), line breaks (div), line breaks (br) -> line breaks
    text = re.sub(r"</p>", r"\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", r"\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", r"\n", text, flags=re.IGNORECASE)

    # Bold (b, strong) -> **text**
    text = re.sub(r"<(b|strong)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.IGNORECASE)

    # Remove all other HTML tags (keep the content)
    text = re.sub(r"<[^>]+>", "", text)

    # Organize consecutive blank lines (reduce 3 or more line breaks to 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_content(entry: dict[str, Any], last_entry_time_loaded: datetime) -> tuple[datetime, str]:
    """Extract Markdown-formatted text content from an entry"""

    time_str = entry.get("time", "")
    dt: datetime = datetime.min.replace(tzinfo=timezone.utc)  # Default value
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if dt <= last_entry_time_loaded:
            return dt, ""  # Skip already processed entries
        formatted_date = dt.strftime("%Y/%m/%d %H:%M:%S")
    except ValueError:
        formatted_date = time_str

    md_output = f"## {formatted_date}\n\n"

    # 1. Action
    title = entry.get("title", "")
    if title:
        md_output += f"**Action**: {title}\n\n"

    # 2. User Prompt (subtitles)
    subtitles = entry.get("subtitles", [])
    if subtitles:
        for item in subtitles:
            name = item.get("name", "User")
            value = item.get("value", "")
            if value:
                # Format in Markdown
                md_output += f"### {name}\n"
                formatted_value = value.replace(chr(10), "  \n")  # Replace line breaks for Markdown
                md_output += f"{formatted_value}\n\n"

    # 3. Gemini Response (safeHtmlItem)
    safe_html_item = entry.get("safeHtmlItem", [])
    if safe_html_item:
        response_text = ""
        for item in safe_html_item:
            html = item.get("html", "")
            if html:
                # Convert HTML to text/Markdown and concatenate
                converted_text = html_to_markdown(html)
                response_text += converted_text + "\n\n"

        # Output header only if there is content
        if response_text.strip():
            md_output += "### Gemini (Response)\n"
            md_output += f"{response_text}\n"

    md_output += "---\n\n"  # Separator
    return dt, md_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Google Takeout JSON to Markdown for NotebookLM")
    parser.add_argument(
        "--input_file", metavar="FILE", type=str, default="MyActivity.json", help="Path to input JSON file"
    )
    parser.add_argument(
        "--output_file",
        metavar="FILE",
        type=str,
        default="Gemini_History.md",
        help="Path to output Markdown file",
    )
    parser.add_argument("--limit", type=int, default=1000000, help="Split file size limit in bytes")

    args = parser.parse_args()
    input_json_filename: str = args.input_file
    output_md_filename: str = args.output_file
    md_file_size_limit: int = args.limit

    try:
        print(t("start_processing", input_json_filename))

        data = load_json(input_json_filename)
        if not data:
            return 1

        # Filter only "Gemini" related activities
        gemini_entries: list[dict[str, Any]] = [
            entry for entry in data if "Gemini" in entry.get("header", "")
        ]

        print(t("extracted_entries", len(data), len(gemini_entries)))
        print(t("converting_markdown"))

        gemini_entries.reverse()

        last_entry_time_loaded, force_full_regeneration = load_last_entry_time(LAST_ENTRY_TIME_FILE)
        last_entry_time_processed: datetime = datetime.min.replace(tzinfo=timezone.utc)

        base_name, ext = os.path.splitext(output_md_filename)

        def get_output_filename(idx: int) -> str:
            return f"{base_name}-{idx:02d}{ext}"

        file_index = 1
        is_append_mode = False
        if force_full_regeneration:
            removed_count = remove_numbered_output_files(base_name, ext)
            if removed_count:
                print_warning("warning_removed_existing_outputs", removed_count)
        else:
            while os.path.exists(get_output_filename(file_index)):
                is_append_mode = True
                file_index += 1
                output_filename = get_output_filename(file_index)
            if file_index > 1:
                file_index -= 1  # Use the last existing file for appending
        output_filename = get_output_filename(file_index)
        current_file_size = 0
        if is_append_mode:
            current_file_size = os.path.getsize(output_filename)

        header = "# Gemini Chat History Archive\n\n"
        header += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        def write_file(output_filename: str, header: str, texts: list[str], is_append_mode: bool) -> None:
            mode = "a" if is_append_mode else "w"
            with open(output_filename, mode, encoding="utf-8") as f:
                if not is_append_mode:
                    f.write(header)
                for text in texts:
                    f.write(text)

        texts = []
        if not is_append_mode:
            current_file_size += len(header.encode("utf-8"))

        for _, entry in enumerate(gemini_entries):
            dt, text = extract_text_content(entry, last_entry_time_loaded)
            if text == "":
                continue
            last_entry_time_processed = dt
            text_size = len(text.encode("utf-8"))

            if current_file_size + text_size > md_file_size_limit:
                if texts:
                    write_file(output_filename, header, texts, is_append_mode)
                    print(
                        t("appended_to_file", output_filename)
                        if is_append_mode
                        else t("written_to_file", output_filename)
                    )
                file_index += 1
                output_filename = get_output_filename(file_index)
                is_append_mode = False
                texts = []
                current_file_size = len(header.encode("utf-8"))

            texts.append(text)
            current_file_size += text_size

        if texts:
            write_file(output_filename, header, texts, is_append_mode)
            print(
                t("appended_to_file", output_filename)
                if is_append_mode
                else t("written_to_file", output_filename)
            )

        if last_entry_time_loaded < last_entry_time_processed:
            with open(LAST_ENTRY_TIME_FILE, "w", encoding="utf-8") as f:
                f.write(last_entry_time_processed.isoformat())

        print(t("processing_complete", last_entry_time_loaded, last_entry_time_processed, file_index))
        return 0
    except Exception as e:
        print_error(t("error_occurred", e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
