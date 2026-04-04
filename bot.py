import os
import re
import tempfile
import subprocess
import speech_recognition as sr
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

# Google STT language codes (maps our internal code to Google's BCP-47)
STT_LANG_MAP = {
    "km": "km-KH", "th": "th-TH", "ar": "ar-SA", "hi": "hi-IN",
    "bn": "bn-BD", "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN",
    "ta": "ta-IN", "te": "te-IN", "ru": "ru-RU", "el": "el-GR",
    "hy": "hy-AM", "ko": "ko-KR", "ja": "ja-JP", "zh-CN": "zh-CN",
    "zh-TW": "zh-TW", "fr": "fr-FR", "de": "de-DE", "es": "es-ES",
    "pt": "pt-BR", "it": "it-IT", "nl": "nl-NL", "pl": "pl-PL",
    "tr": "tr-TR", "vi": "vi-VN", "id": "id-ID", "my": "my-MM",
    "ne": "ne-NP", "si": "si-LK", "ur": "ur-PK", "sw": "sw-TZ",
    "uk": "uk-UA", "ro": "ro-RO", "hu": "hu-HU", "cs": "cs-CZ",
    "sv": "sv-SE", "da": "da-DK", "fi": "fi-FI", "no": "no-NO",
    "en": "en-US",
}

SCRIPT_LANG_MAP = [
    (r'[\u1780-\u17FF]', 'km'),
    (r'[\u0E00-\u0E7F]', 'th'),
    (r'[\u0600-\u06FF]', 'ar'),
    (r'[\u0900-\u097F]', 'hi'),
    (r'[\u0980-\u09FF]', 'bn'),
    (r'[\u0A80-\u0AFF]', 'gu'),
    (r'[\u0C80-\u0CFF]', 'kn'),
    (r'[\u0D00-\u0D7F]', 'ml'),
    (r'[\u0B80-\u0BFF]', 'ta'),
    (r'[\u0C00-\u0C7F]', 'te'),
    (r'[\u0400-\u04FF]', 'ru'),
    (r'[\u0370-\u03FF]', 'el'),
    (r'[\u0530-\u058F]', 'hy'),
    (r'[\u0590-\u05FF]', 'iw'),
    (r'[\u0E80-\u0EFF]', 'lo'),
    (r'[\u1000-\u109F]', 'my'),
    (r'[\u0D80-\u0DFF]', 'si'),
    (r'[\uAC00-\uD7FF]', 'ko'),
    (r'[\u3040-\u30FF]', 'ja'),
    (r'[\u4E00-\u9FFF]', 'zh-CN'),
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

def ogg_to_wav(ogg_path: str, wav_path: str):
    subprocess.run(
        ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    await update.message.reply_text(
        "Hello! I'm a Text-to-Voice bot.\n\n"
        "You can:\n"
        "1. Send me TEXT → I'll convert it to a voice message\n"
        "2. Send me a VOICE message → I'll transcribe it and read it back\n\n"
        "I support Khmer, English, Arabic, Chinese, French, Spanish, Hindi, Japanese, Korean, Russian, Thai, and 50+ more languages!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n\n"
        "Text → Voice:\nJust send any text message. I detect the language automatically and reply with a voice message.\n\n"
        "Voice → Text + Voice:\nSend me a voice message. I'll transcribe it and read it back to you.\n\n"
        "Examples:\n"
        "- Hello world  (English)\n"
        "- សួស្ដី (Khmer)\n"
        "- مرحبا (Arabic)\n"
        "- 你好 (Chinese)"
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
                caption=f"Language: {lang_name}"
            )

        os.unlink(tmp_path)

    except Exception as e:
        print(f"TTS Error: {e}")
        await update.message.reply_text("Sorry, I couldn't convert that text to speech. Please try again.")

async def voice_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)

    ogg_path = None
    wav_path = None

    try:
        voice = update.message.voice or update.message.audio
        tg_file = await context.bot.get_file(voice.file_id)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_tmp:
            ogg_path = ogg_tmp.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_tmp:
            wav_path = wav_tmp.name

        await tg_file.download_to_drive(ogg_path)
        ogg_to_wav(ogg_path, wav_path)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)

        # Try Khmer first, then auto-detect with English fallback
        transcribed_text = None
        detected_lang = "km"

        try_langs = ["km-KH", "en-US", "zh-CN", "fr-FR", "ar-SA", "th-TH", "ko-KR", "ja-JP"]

        for lang_code in try_langs:
            try:
                transcribed_text = recognizer.recognize_google(audio_data, language=lang_code)
                if transcribed_text:
                    break
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"STT request error: {e}")
                break

        if not transcribed_text:
            await update.message.reply_text(
                "I couldn't understand the audio. Please speak clearly and try again."
            )
            return

        detected_lang = detect_language(transcribed_text)
        lang_name = LANG_NAMES.get(detected_lang, detected_lang.upper())

        await update.message.reply_text(f"Transcribed ({lang_name}):\n{transcribed_text}")

        await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.RECORD_VOICE)

        tts = gTTS(text=transcribed_text, lang=detected_lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tts_tmp:
            tts_path = tts_tmp.name
            tts.save(tts_path)

        with open(tts_path, "rb") as audio_file:
            await update.message.reply_voice(
                voice=audio_file,
                caption=f"Voice reply in {lang_name}"
            )

        os.unlink(tts_path)

    except Exception as e:
        print(f"Voice Error: {e}")
        await update.message.reply_text("Sorry, something went wrong processing your voice message. Please try again.")

    finally:
        if ogg_path and os.path.exists(ogg_path):
            os.unlink(ogg_path)
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_voice))
app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_to_text))
app.run_polling()
