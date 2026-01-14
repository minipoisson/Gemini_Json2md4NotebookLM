import argparse
import contextlib
import html as html_module
import json
import locale
import os
import re
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
    },
    "hi": {
        "error_lang_detection": "त्रुटि: सिस्टम भाषा का पता लगाने में समस्या: {}",
        "file_not_found": "त्रुटि: फ़ाइल नहीं मिली: {}",
        "json_decode_error": "JSON डिकोड त्रुटि: {}",
        "start_processing": "🚀 प्रसंस्करण शुरू हो रहा है: {} लोड हो रहा है...",
        "extracted_entries": "Ditemukan {0} entri, di mana {1} adalah riwayat Gemini.",
        "converting_markdown": "Mengonversi ke Markdown...",
        "appended_to_file": "Riwayat obrolan ditambahkan ke file: {}",
        "written_to_file": "Riwayat obrolan ditulis ke file: {}",
        "processing_complete": "✅ Selesai: Riwayat disimpan dari {0} hingga {1} dalam total {2} file.",
        "error_occurred": "Terjadi kesalahan: {}",
    },
    "id": {
        "error_lang_detection": "Error saat mendeteksi bahasa sistem: {}",
        "file_not_found": "Error: File tidak ditemukan: {}",
        "json_decode_error": "Error decode JSON: {}",
        "start_processing": "🚀 Memulai pemrosesan: Memuat {}...",
        "extracted_entries": "Estratti {0} voci, di cui {1} sono cronologia di Gemini.",
        "converting_markdown": "Conversione in Markdown...",
        "appended_to_file": "Cronologia chat aggiunta al file: {}",
        "written_to_file": "Cronologia chat scritta nel file: {}",
        "processing_complete": "✅ Completato: Cronologia salvata da {0} a {1} in un totale di {2} file.",
        "error_occurred": "Si è verificato un errore: {}",
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
        "processing_complete": "✅ पूर्ण झाले: इतिहास {0} पासून {1} पर्यंत एकूण {2} फाइलमध्ये जतन केला गेला.",
        "error_occurred": "एक त्रुटी आली आहे: {}",
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
    },
    "ta": {
        "error_lang_detection": "சிஸ்டம் மொழியை கண்டறிதலில் பிழை: {}",
        "file_not_found": "பிழை: கோப்பு காணப்படவில்லை: {}",
        "json_decode_error": "JSON குறியாக்க பிழை: {}",
        "start_processing": "🚀 செயலாக்கம் தொடங்குகிறது: {} ஏற்றப்படுகிறது...",
        "extracted_entries": "ดึงข้อมูล {0} รายการ ซึ่งมีประวัติของ Gemini จำนวน {1} รายการ",
        "converting_markdown": "กำลังแปลงเป็น Markdown...",
        "appended_to_file": "ประวัติการแชทถูกเพิ่มลงในไฟล์: {}",
        "written_to_file": "ประวัติการแชทถูกเขียนลงในไฟล์: {}",
        "processing_complete": "✅ เสร็จสิ้น: บันทึกประวัติจาก {0} ถึง {1} ลงในไฟล์ทั้งหมด {2} ไฟล์",
        "error_occurred": "เกิดข้อผิดพลาด: {}",
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
    },
    "ur": {
        "error_lang_detection": "سسٹم زبان کا پتہ لگانے میں خرابی: {}",
        "file_not_found": "خرابی: فائل نہیں ملی: {}",
        "json_decode_error": "JSON ڈی کوڈنگ کی خرابی: {}",
        "start_processing": "🚀 پراسیسنگ شروع ہو رہی ہے: {} لوڈ ہو رہا ہے...",
        "extracted_entries": "{0} اندراجات نکالے گئے، جن میں سے {1} Gemini کی تاریخ ہے۔",
        "converting_markdown": "Markdown میں تبدیل کیا جا رہا ہے...",
        "appended_to_file": "چیٹ کی تاریخ فائل میں شامل کر دی گئی ہے: {}",
        "written_to_file": "چیٹ کی تاریخ فائل میں لکھ دی گئی ہے: {}",
        "processing_complete": "✅ مکمل ہو گیا: تاریخ {0} سے {1} تک کل {2} فائلوں میں محفوظ کر دی گئی ہے۔",
        "error_occurred": "ایک خرابی پیش آئی: {}",
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
    },
}


def get_system_language() -> str:
    """detect OS language setting"""
    try:
        lang_tuple = locale.getlocale()
        if lang_tuple[0]:
            lang_name = lang_tuple[0].split("_")[0]
            lang_code = LANG_MAP.get(lang_name, lang_name[:2].lower())
        else:
            lang_code = None

        if lang_code is None:
            return "en"

        if lang_code == "zh_CN" or lang_code == "zh-Hans" or lang_name == "Chinese_China":
            return "zh_CN"
        elif lang_code == "zh_TW" or lang_code == "zh-Hant" or lang_name == "Chinese_Taiwan":
            return "zh_TW"

        lang_code = lang_code.split("_")[0].split("-")[0].lower()
        if lang_code in TRANSLATIONS:
            return lang_code
        return "en"

    except Exception as e:
        error_msg = TRANSLATIONS.get("en", {}).get("error_lang_detection", "Error: {}")
        print(error_msg.format(e))
        return "en"


def t(key: str, *args: Any) -> str:
    """Translation function"""
    lang = get_system_language()

    msg_map: dict[str, str] = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    msg: str = msg_map.get(key, TRANSLATIONS["en"].get(key, key))

    if args:
        try:
            return msg.format(*args)
        except IndexError:
            # Safety measure in case the number of placeholders and variables do not match
            return msg
    return msg


def load_json(filepath: str) -> list[dict[str, Any]]:
    """Load a JSON file"""
    if not os.path.exists(filepath):
        print(t("file_not_found", filepath))
        return []

    with open(filepath, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(t("json_decode_error", e))
            return []


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
    safeHtmlItem = entry.get("safeHtmlItem", [])
    if safeHtmlItem:
        response_text = ""
        for item in safeHtmlItem:
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


def main() -> None:
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
    parser.add_argument("--limit", type=int, default=1500000, help="Split file size limit in bytes")

    args = parser.parse_args()
    input_json_filename: str = args.input_file
    output_md_filename: str = args.output_file
    md_file_size_limit: int = args.limit

    try:
        print(t("start_processing", input_json_filename))

        data = load_json(input_json_filename)
        if not data:
            return

        # Filter only "Gemini" related activities
        gemini_entries: list[dict[str, Any]] = [
            entry for entry in data if "Gemini" in entry.get("header", "")
        ]

        print(t("extracted_entries", len(data), len(gemini_entries)))
        print(t("converting_markdown"))

        gemini_entries.reverse()

        last_entry_time_loaded: datetime = datetime.min.replace(tzinfo=timezone.utc)
        last_entry_time_processed: datetime = datetime.min.replace(tzinfo=timezone.utc)
        if os.path.exists(LAST_ENTRY_TIME_FILE):
            with open(LAST_ENTRY_TIME_FILE, encoding="utf-8") as f:
                time_str = f.read().strip()
                with contextlib.suppress(ValueError):
                    last_entry_time_loaded = datetime.fromisoformat(time_str)

        base_name, ext = os.path.splitext(output_md_filename)

        def get_output_filename(idx: int) -> str:
            return f"{base_name}-{idx:02d}{ext}"

        file_index = 1
        is_append_mode = False
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
                f.write(header)
                for text in texts:
                    f.write(text)

        texts = []
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
    except Exception as e:
        print(t("error_occurred", e))


if __name__ == "__main__":
    main()
