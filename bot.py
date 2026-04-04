import os
import re
import tempfile
import edge_tts
from langdetect import detect as langdetect_detect, DetectorFactory
from telegram import Update, constants, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

DetectorFactory.seed = 0

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

MALE_VOICES = {
    "km":    "km-KH-PisethNeural",
    "en":    "en-US-GuyNeural",
    "ar":    "ar-SA-HamedNeural",
    "zh-CN": "zh-CN-YunxiNeural",
    "zh-TW": "zh-TW-YunJheNeural",
    "fr":    "fr-FR-HenriNeural",
    "de":    "de-DE-ConradNeural",
    "es":    "es-ES-AlvaroNeural",
    "hi":    "hi-IN-MadhurNeural",
    "ja":    "ja-JP-KeitaNeural",
    "ko":    "ko-KR-InJoonNeural",
    "pt":    "pt-BR-AntonioNeural",
    "ru":    "ru-RU-DmitryNeural",
    "th":    "th-TH-NiwatNeural",
    "vi":    "vi-VN-NamMinhNeural",
    "id":    "id-ID-ArdiNeural",
    "tr":    "tr-TR-AhmetNeural",
    "pl":    "pl-PL-MarekNeural",
    "nl":    "nl-NL-MaartenNeural",
    "it":    "it-IT-DiegoNeural",
    "sv":    "sv-SE-MattiasNeural",
    "da":    "da-DK-JeppeNeural",
    "fi":    "fi-FI-HarriNeural",
    "no":    "nb-NO-FinnNeural",
    "cs":    "cs-CZ-AntoninNeural",
    "ro":    "ro-RO-EmilNeural",
    "hu":    "hu-HU-TamasNeural",
    "uk":    "uk-UA-OstapNeural",
    "el":    "el-GR-NestorasNeural",
    "bn":    "bn-BD-PradeepNeural",
    "ta":    "ta-IN-ValluvarNeural",
    "te":    "te-IN-MohanNeural",
    "ur":    "ur-PK-AsadNeural",
    "my":    "my-MM-ThihaNeural",
    "ne":    "ne-NP-SagarNeural",
    "af":    "af-ZA-WillemNeural",
    "sw":    "sw-KE-RafikiNeural",
    "sk":    "sk-SK-LukasNeural",
    "hr":    "hr-HR-SreckoNeural",
    "bg":    "bg-BG-BorislavNeural",
    "ms":    "ms-MY-OsmanNeural",
    "gu":    "gu-IN-NiranjanNeural",
    "mr":    "mr-IN-ManoharNeural",
    "iw":    "he-IL-AvriNeural",
}

FEMALE_VOICES = {
    "km":    "km-KH-SreymomNeural",
    "en":    "en-US-JennyNeural",
    "ar":    "ar-SA-ZariyahNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "fr":    "fr-FR-DeniseNeural",
    "de":    "de-DE-KatjaNeural",
    "es":    "es-ES-ElviraNeural",
    "hi":    "hi-IN-SwaraNeural",
    "ja":    "ja-JP-NanamiNeural",
    "ko":    "ko-KR-SunHiNeural",
    "pt":    "pt-BR-FranciscaNeural",
    "ru":    "ru-RU-SvetlanaNeural",
    "th":    "th-TH-PremwadeeNeural",
    "vi":    "vi-VN-HoaiMyNeural",
    "id":    "id-ID-GadisNeural",
    "tr":    "tr-TR-EmelNeural",
    "pl":    "pl-PL-ZofiaNeural",
    "nl":    "nl-NL-ColetteNeural",
    "it":    "it-IT-ElsaNeural",
    "sv":    "sv-SE-SofieNeural",
    "da":    "da-DK-ChristelNeural",
    "fi":    "fi-FI-NooraNeural",
    "no":    "nb-NO-PernilleNeural",
    "cs":    "cs-CZ-VlastaNeural",
    "ro":    "ro-RO-AlinaNeural",
    "hu":    "hu-HU-NoemiNeural",
    "uk":    "uk-UA-PolinaNeural",
    "el":    "el-GR-AthinaNeural",
    "bn":    "bn-BD-NabanitaNeural",
    "ta":    "ta-IN-PallaviNeural",
    "te":    "te-IN-ShrutiNeural",
    "ml":    "ml-IN-SobhanaNeural",
    "ur":    "ur-PK-UzmaNeural",
    "my":    "my-MM-NilarNeural",
    "ne":    "ne-NP-HemkalaNeural",
    "si":    "si-LK-ThiliniNeural",
    "af":    "af-ZA-AdriNeural",
    "sw":    "sw-KE-ZuriNeural",
    "sk":    "sk-SK-ViktoriaNeural",
    "hr":    "hr-HR-GabrijelaNeural",
    "bg":    "bg-BG-KalinaNeural",
    "ms":    "ms-MY-YasminNeural",
    "gu":    "gu-IN-DhwaniNeural",
    "mr":    "mr-IN-AarohiNeural",
    "iw":    "he-IL-HilaNeural",
}

LANG_NAMES = {
    "km": "ខ្មែរ (Khmer)", "en": "English", "ar": "Arabic", "zh-CN": "Chinese",
    "zh-TW": "Chinese (Traditional)", "fr": "French", "de": "German",
    "es": "Spanish", "hi": "Hindi", "ja": "Japanese", "ko": "Korean",
    "pt": "Portuguese", "ru": "Russian", "th": "Thai", "vi": "Vietnamese",
    "id": "Indonesian", "tr": "Turkish", "pl": "Polish", "nl": "Dutch",
    "it": "Italian", "sv": "Swedish", "da": "Danish", "fi": "Finnish",
    "no": "Norwegian", "cs": "Czech", "ro": "Romanian", "hu": "Hungarian",
    "uk": "Ukrainian", "el": "Greek", "bn": "Bengali", "ta": "Tamil",
    "te": "Telugu", "ml": "Malayalam", "ur": "Urdu", "my": "Myanmar",
    "ne": "Nepali", "si": "Sinhala", "af": "Afrikaans", "sw": "Swahili",
    "sk": "Slovak", "hr": "Croatian", "bg": "Bulgarian", "ms": "Malay",
    "gu": "Gujarati", "mr": "Marathi", "iw": "Hebrew",
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

GENDER_KEY = "voice_gender"

def get_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("👨 សំឡេងប្រុស"), KeyboardButton("👩 សំឡេងស្រី")]],
        resize_keyboard=True,
        persistent=True
    )

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

async def synthesize(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if GENDER_KEY not in context.user_data:
        context.user_data[GENDER_KEY] = "female"
    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.TYPING)
    await update.message.reply_text(
        "សួស្ដី! ខ្ញុំជា Text-to-Voice Bot 🎙️\n\n"
        "ផ្ញើអត្ថបទណាមួយ ហើយខ្ញុំបំប្លែងជាសំឡេង!\n"
        "ជ្រើសរើសសំឡេងប្រុស ឬស្រីដោយប្រើប៊ូតុងខាងក្រោម។\n\n"
        "Send any text in any language and I'll speak it!\n"
        "Choose male or female voice using the buttons below.",
        reply_markup=get_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👨 សំឡេងប្រុស":
        context.user_data[GENDER_KEY] = "male"
        await update.message.reply_text("✅ បានប្តូរទៅសំឡេងប្រុស (Male voice)", reply_markup=get_keyboard())
        return

    if text == "👩 សំឡេងស្រី":
        context.user_data[GENDER_KEY] = "female"
        await update.message.reply_text("✅ បានប្តូរទៅសំឡេងស្រី (Female voice)", reply_markup=get_keyboard())
        return

    await context.bot.send_chat_action(update.effective_chat.id, constants.ChatAction.RECORD_VOICE)

    try:
        detected_lang = detect_language(text)
        gender = context.user_data.get(GENDER_KEY, "female")

        voice_map = MALE_VOICES if gender == "male" else FEMALE_VOICES
        voice = voice_map.get(detected_lang, FEMALE_VOICES.get(detected_lang, "en-US-JennyNeural"))

        lang_name = LANG_NAMES.get(detected_lang, detected_lang.upper())
        gender_label = "👨 ប្រុស" if gender == "male" else "👩 ស្រី"

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        await synthesize(text, voice, tmp_path)

        with open(tmp_path, "rb") as audio_file:
            await update.message.reply_voice(
                voice=audio_file,
                caption=f"🌐 {lang_name} | {gender_label}",
                reply_markup=get_keyboard()
            )

        os.unlink(tmp_path)

    except Exception as e:
        print(f"TTS Error: {e}")
        await update.message.reply_text(
            "Sorry, I couldn't convert that text to speech. Please try again.",
            reply_markup=get_keyboard()
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
