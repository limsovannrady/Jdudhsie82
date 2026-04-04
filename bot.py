import os
import re
import tempfile
from gtts import gTTS
from langdetect import detect as langdetect_detect, DetectorFactory
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DetectorFactory.seed = 0

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

LANG_NAMES = {
    "af": "Afrikaans", "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali",
    "bs": "Bosnian", "ca": "Catalan", "cs": "Czech", "cy": "Welsh",
    "da": "Danish", "de": "German", "el": "Greek", "en": "English",
    "eo": "Esperanto", "es": "Spanish", "et": "Estonian", "fi": "Finnish",
    "fr": "French", "gu": "Gujarati", "hi": "Hindi", "hr": "Croatian",
    "hu": "Hungarian", "hy": "Armenian", "id": "Indonesian", "is": "Icelandic",
    "it": "Italian", "ja": "Japanese", "jw": "Javanese", "km": "Khmer",
    "kn": "Kannada", "ko": "Korean", "la": "Latin", "lv": "Latvian",
    "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "my": "Myanmar",
    "ne": "Nepali", "nl": "Dutch", "no": "Norwegian", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "si": "Sinhala",
    "sk": "Slovak", "sq": "Albanian", "sr": "Serbian", "su": "Sundanese",
    "sv": "Swedish", "sw": "Swahili", "ta": "Tamil", "te": "Telugu",
    "th": "Thai", "tl": "Filipino", "tr": "Turkish", "uk": "Ukrainian",
    "ur": "Urdu", "vi": "Vietnamese", "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)"
}

SCRIPT_LANG_MAP = [
    (r'[\u1780-\u17FF]', 'km'),        # Khmer
    (r'[\u0E00-\u0E7F]', 'th'),        # Thai
    (r'[\u0600-\u06FF]', 'ar'),        # Arabic
    (r'[\u0900-\u097F]', 'hi'),        # Devanagari → Hindi
    (r'[\u0980-\u09FF]', 'bn'),        # Bengali
    (r'[\u0A80-\u0AFF]', 'gu'),        # Gujarati
    (r'[\u0C80-\u0CFF]', 'kn'),        # Kannada
    (r'[\u0D00-\u0D7F]', 'ml'),        # Malayalam
    (r'[\u0B80-\u0BFF]', 'ta'),        # Tamil
    (r'[\u0C00-\u0C7F]', 'te'),        # Telugu
    (r'[\u0400-\u04FF]', 'ru'),        # Cyrillic → Russian
    (r'[\u0370-\u03FF]', 'el'),        # Greek
    (r'[\u0530-\u058F]', 'hy'),        # Armenian
    (r'[\u10A0-\u10FF]', 'ka'),        # Georgian
    (r'[\u0700-\u074F]', 'ur'),        # Syriac/Urdu hint
    (r'[\u0750-\u077F]', 'ar'),        # Arabic Supplement
    (r'[\uFB50-\uFDFF]', 'ar'),        # Arabic Presentation
    (r'[\u0590-\u05FF]', 'iw'),        # Hebrew
    (r'[\u0E80-\u0EFF]', 'lo'),        # Lao
    (r'[\u1000-\u109F]', 'my'),        # Myanmar/Burmese
    (r'[\u0D80-\u0DFF]', 'si'),        # Sinhala
    (r'[\uAC00-\uD7FF]', 'ko'),        # Korean Hangul
    (r'[\u3040-\u30FF]', 'ja'),        # Japanese Hiragana/Katakana
    (r'[\u4E00-\u9FFF]', 'zh-CN'),     # CJK (Chinese/Japanese/Korean)
    (r'[\u0900-\u097F]', 'ne'),        # Devanagari can be Nepali too
]

def detect_language(text: str) -> str:
    for pattern, lang in SCRIPT_LANG_MAP:
        if re.search(pattern, text):
            return lang
    try:
        detected = langdetect_detect(text)
        if detected in ('zh-cn', 'zh'):
            return 'zh-CN'
        if detected == 'zh-tw':
            return 'zh-TW'
        return detected
    except Exception:
        return 'en'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    await update.message.reply_text(
        "Hello! I'm a Text-to-Voice bot.\n\n"
        "Send me any text in any language and I'll convert it to speech!\n\n"
        "Supports: Khmer, English, Arabic, Chinese, French, Spanish, Hindi, Japanese, Korean, Russian, Thai, and 50+ more languages."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send me any text message and I'll read it aloud!\n\n"
        "I automatically detect the language — no setup needed.\n\n"
        "Examples:\n"
        "- Hello world  (English)\n"
        "- សួស្ដី (Khmer)\n"
        "- مرحبا بالعالم (Arabic)\n"
        "- 你好世界 (Chinese)\n"
        "- Bonjour le monde (French)"
    )

async def text_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.RECORD_VOICE)

    try:
        detected_lang = detect_language(text)

        tts = gTTS(text=text, lang=detected_lang, slow=False)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
            tts.save(tmp_path)

        lang_name = LANG_NAMES.get(detected_lang, detected_lang.upper())

        with open(tmp_path, "rb") as audio_file:
            await update.message.reply_voice(
                voice=audio_file,
                caption=f"Language detected: {lang_name}"
            )

        os.unlink(tmp_path)

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {e}")
        if "Language not supported" in error_msg or "is not supported" in error_msg:
            await update.message.reply_text(
                "Sorry, this language is not supported for text-to-speech yet."
            )
        else:
            await update.message.reply_text(
                "Sorry, I couldn't convert that text to speech. Please try again."
            )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_voice))
app.run_polling()
