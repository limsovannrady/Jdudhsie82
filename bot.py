import os
import tempfile
from gtts import gTTS
from langdetect import detect, DetectorFactory
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
    "zh-TW": "Chinese (Traditional)", "km": "Khmer"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    await update.message.reply_text(
        "Hello! I'm a Text-to-Voice bot.\n\n"
        "Send me any text in any language and I'll convert it to speech!\n\n"
        "Supported: English, Arabic, Chinese, French, Spanish, Hindi, Japanese, Korean, Russian, and 50+ more languages."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just send me any text message and I'll read it aloud for you!\n\n"
        "I automatically detect the language, so no setup needed.\n\n"
        "Example:\n"
        "- Hello world\n"
        "- مرحبا بالعالم\n"
        "- 你好世界\n"
        "- Bonjour le monde"
    )

async def text_to_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.RECORD_VOICE)

    try:
        detected_lang = detect(text)

        gtts_lang = detected_lang
        if detected_lang == "zh-cn":
            gtts_lang = "zh-CN"
        elif detected_lang == "zh-tw":
            gtts_lang = "zh-TW"

        tts = gTTS(text=text, lang=gtts_lang, slow=False)

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
        if "Language not supported" in error_msg or "is not supported" in error_msg:
            await update.message.reply_text(
                f"Sorry, this language is not supported for text-to-speech yet."
            )
        else:
            await update.message.reply_text(
                "Sorry, I couldn't convert that text to speech. Please try again."
            )
        print(f"Error: {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_voice))
app.run_polling()
