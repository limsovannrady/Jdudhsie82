import os
import re
import asyncio
import logging
from io import BytesIO
from collections import OrderedDict
import edge_tts
from langdetect import detect as langdetect_detect, detect_langs, DetectorFactory
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyParameters, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

# Cache Telegram file_id for repeated text — avoids re-upload (instant resend)
_FILE_ID_CACHE: OrderedDict[str, str] = OrderedDict()
_CACHE_MAX = 200

def _cache_get(key: str):
    if key in _FILE_ID_CACHE:
        _FILE_ID_CACHE.move_to_end(key)
        return _FILE_ID_CACHE[key]
    return None

def _cache_set(key: str, file_id: str):
    if key in _FILE_ID_CACHE:
        _FILE_ID_CACHE.move_to_end(key)
    else:
        if len(_FILE_ID_CACHE) >= _CACHE_MAX:
            _FILE_ID_CACHE.popitem(last=False)
        _FILE_ID_CACHE[key] = file_id

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

DetectorFactory.seed = 0

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# All available edge-tts voices — male and female per language
MALE_VOICES = {
    "af":    "af-ZA-WillemNeural",
    "am":    "am-ET-AmehaNeural",
    "ar":    "ar-SA-HamedNeural",
    "az":    "az-AZ-BabekNeural",
    "bg":    "bg-BG-BorislavNeural",
    "bn":    "bn-BD-PradeepNeural",
    "bs":    "bs-BA-GoranNeural",
    "ca":    "ca-ES-EnricNeural",
    "cs":    "cs-CZ-AntoninNeural",
    "cy":    "cy-GB-AledNeural",
    "da":    "da-DK-JeppeNeural",
    "de":    "de-DE-ConradNeural",
    "el":    "el-GR-NestorasNeural",
    "en":    "en-US-GuyNeural",
    "es":    "es-ES-AlvaroNeural",
    "et":    "et-EE-KertNeural",
    "fa":    "fa-IR-FaridNeural",
    "fi":    "fi-FI-HarriNeural",
    "fil":   "fil-PH-AngeloNeural",
    "fr":    "fr-FR-HenriNeural",
    "ga":    "ga-IE-ColmNeural",
    "gl":    "gl-ES-RoiNeural",
    "gu":    "gu-IN-NiranjanNeural",
    "he":    "he-IL-AvriNeural",
    "hi":    "hi-IN-MadhurNeural",
    "hr":    "hr-HR-SreckoNeural",
    "hu":    "hu-HU-TamasNeural",
    "id":    "id-ID-ArdiNeural",
    "is":    "is-IS-GunnarNeural",
    "it":    "it-IT-DiegoNeural",
    "ja":    "ja-JP-KeitaNeural",
    "jv":    "jv-ID-DimasNeural",
    "ka":    "ka-GE-GiorgiNeural",
    "kk":    "kk-KZ-DauletNeural",
    "km":    "km-KH-PisethNeural",
    "kn":    "kn-IN-GaganNeural",
    "ko":    "ko-KR-InJoonNeural",
    "lo":    "lo-LA-ChanthavongNeural",
    "lt":    "lt-LT-LeonasNeural",
    "lv":    "lv-LV-NilsNeural",
    "mk":    "mk-MK-AleksandarNeural",
    "ml":    "ml-IN-MidhunNeural",
    "mn":    "mn-MN-BataaNeural",
    "mr":    "mr-IN-ManoharNeural",
    "ms":    "ms-MY-OsmanNeural",
    "mt":    "mt-MT-JosephNeural",
    "my":    "my-MM-ThihaNeural",
    "nb":    "nb-NO-FinnNeural",
    "ne":    "ne-NP-SagarNeural",
    "nl":    "nl-NL-MaartenNeural",
    "pl":    "pl-PL-MarekNeural",
    "ps":    "ps-AF-GulNawazNeural",
    "pt":    "pt-BR-AntonioNeural",
    "ro":    "ro-RO-EmilNeural",
    "ru":    "ru-RU-DmitryNeural",
    "si":    "si-LK-SameeraNeural",
    "sk":    "sk-SK-LukasNeural",
    "sl":    "sl-SI-RokNeural",
    "so":    "so-SO-MuuseNeural",
    "sq":    "sq-AL-IlirNeural",
    "sr":    "sr-RS-NicholasNeural",
    "su":    "su-ID-JajangNeural",
    "sv":    "sv-SE-MattiasNeural",
    "sw":    "sw-KE-RafikiNeural",
    "ta":    "ta-IN-ValluvarNeural",
    "te":    "te-IN-MohanNeural",
    "th":    "th-TH-NiwatNeural",
    "tr":    "tr-TR-AhmetNeural",
    "uk":    "uk-UA-OstapNeural",
    "ur":    "ur-IN-SalmanNeural",
    "uz":    "uz-UZ-SardorNeural",
    "vi":    "vi-VN-NamMinhNeural",
    "zh-CN": "zh-CN-YunxiNeural",
    "zh-TW": "zh-TW-YunJheNeural",
    "zu":    "zu-ZA-ThembaNeural",
}

FEMALE_VOICES = {
    "af":    "af-ZA-AdriNeural",
    "am":    "am-ET-MekdesNeural",
    "ar":    "ar-SA-ZariyahNeural",
    "az":    "az-AZ-BanuNeural",
    "bg":    "bg-BG-KalinaNeural",
    "bn":    "bn-BD-NabanitaNeural",
    "bs":    "bs-BA-VesnaNeural",
    "ca":    "ca-ES-JoanaNeural",
    "cs":    "cs-CZ-VlastaNeural",
    "cy":    "cy-GB-NiaNeural",
    "da":    "da-DK-ChristelNeural",
    "de":    "de-DE-KatjaNeural",
    "el":    "el-GR-AthinaNeural",
    "en":    "en-US-JennyNeural",
    "es":    "es-ES-ElviraNeural",
    "et":    "et-EE-AnuNeural",
    "fa":    "fa-IR-DilaraNeural",
    "fi":    "fi-FI-NooraNeural",
    "fil":   "fil-PH-BlessicaNeural",
    "fr":    "fr-FR-DeniseNeural",
    "ga":    "ga-IE-OrlaNeural",
    "gl":    "gl-ES-SabelaNeural",
    "gu":    "gu-IN-DhwaniNeural",
    "he":    "he-IL-HilaNeural",
    "hi":    "hi-IN-SwaraNeural",
    "hr":    "hr-HR-GabrijelaNeural",
    "hu":    "hu-HU-NoemiNeural",
    "id":    "id-ID-GadisNeural",
    "is":    "is-IS-GudrunNeural",
    "it":    "it-IT-ElsaNeural",
    "ja":    "ja-JP-NanamiNeural",
    "jv":    "jv-ID-SitiNeural",
    "ka":    "ka-GE-EkaNeural",
    "kk":    "kk-KZ-AigulNeural",
    "km":    "km-KH-SreymomNeural",
    "kn":    "kn-IN-SapnaNeural",
    "ko":    "ko-KR-SunHiNeural",
    "lo":    "lo-LA-KeomanyNeural",
    "lt":    "lt-LT-OnaNeural",
    "lv":    "lv-LV-EveritaNeural",
    "mk":    "mk-MK-MarijaNeural",
    "ml":    "ml-IN-SobhanaNeural",
    "mn":    "mn-MN-YesuiNeural",
    "mr":    "mr-IN-AarohiNeural",
    "ms":    "ms-MY-YasminNeural",
    "mt":    "mt-MT-GraceNeural",
    "my":    "my-MM-NilarNeural",
    "nb":    "nb-NO-PernilleNeural",
    "ne":    "ne-NP-HemkalaNeural",
    "nl":    "nl-NL-ColetteNeural",
    "pl":    "pl-PL-ZofiaNeural",
    "ps":    "ps-AF-LatifaNeural",
    "pt":    "pt-BR-FranciscaNeural",
    "ro":    "ro-RO-AlinaNeural",
    "ru":    "ru-RU-SvetlanaNeural",
    "si":    "si-LK-ThiliniNeural",
    "sk":    "sk-SK-ViktoriaNeural",
    "sl":    "sl-SI-PetraNeural",
    "so":    "so-SO-UbaxNeural",
    "sq":    "sq-AL-AnilaNeural",
    "sr":    "sr-RS-SophieNeural",
    "su":    "su-ID-TutiNeural",
    "sv":    "sv-SE-SofieNeural",
    "sw":    "sw-KE-ZuriNeural",
    "ta":    "ta-IN-PallaviNeural",
    "te":    "te-IN-ShrutiNeural",
    "th":    "th-TH-PremwadeeNeural",
    "tr":    "tr-TR-EmelNeural",
    "uk":    "uk-UA-PolinaNeural",
    "ur":    "ur-IN-GulNeural",
    "uz":    "uz-UZ-MadinaNeural",
    "vi":    "vi-VN-HoaiMyNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "zu":    "zu-ZA-ThandoNeural",
}

LANG_NAMES = {
    "af": "Afrikaans", "am": "Amharic (አማርኛ)", "ar": "Arabic (العربية)",
    "az": "Azerbaijani", "bg": "Bulgarian", "bn": "Bengali (বাংলা)",
    "bs": "Bosnian", "ca": "Catalan", "cs": "Czech", "cy": "Welsh",
    "da": "Danish", "de": "German", "el": "Greek (Ελληνικά)",
    "en": "English", "es": "Spanish", "et": "Estonian",
    "fa": "Persian (فارسی)", "fi": "Finnish", "fil": "Filipino",
    "fr": "French", "ga": "Irish", "gl": "Galician",
    "gu": "Gujarati (ગુજરાતી)", "he": "Hebrew (עברית)", "hi": "Hindi (हिंदी)",
    "hr": "Croatian", "hu": "Hungarian", "id": "Indonesian",
    "is": "Icelandic", "it": "Italian", "ja": "Japanese (日本語)",
    "jv": "Javanese", "ka": "Georgian (ქართული)", "kk": "Kazakh",
    "km": "ខ្មែរ (Khmer)", "kn": "Kannada (ಕನ್ನಡ)", "ko": "Korean (한국어)",
    "lo": "Lao (ລາວ)", "lt": "Lithuanian", "lv": "Latvian",
    "mk": "Macedonian", "ml": "Malayalam (മലയാളം)", "mn": "Mongolian",
    "mr": "Marathi (मराठी)", "ms": "Malay", "mt": "Maltese",
    "my": "Myanmar (မြန်မာ)", "nb": "Norwegian", "ne": "Nepali (नेपाली)",
    "nl": "Dutch", "pl": "Polish", "ps": "Pashto (پښتو)",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian (Русский)",
    "si": "Sinhala (සිංහල)", "sk": "Slovak", "sl": "Slovenian",
    "so": "Somali", "sq": "Albanian", "sr": "Serbian",
    "su": "Sundanese", "sv": "Swedish", "sw": "Swahili",
    "ta": "Tamil (தமிழ்)", "te": "Telugu (తెలుగు)", "th": "Thai (ภาษาไทย)",
    "tr": "Turkish", "uk": "Ukrainian", "ur": "Urdu (اردو)",
    "uz": "Uzbek", "vi": "Vietnamese", "zh-CN": "Chinese (中文简体)",
    "zh-TW": "Chinese (中文繁體)", "zu": "Zulu",
}

# Normalize langdetect output → our internal code
NORMALIZE = {
    "zh-cn": "zh-CN", "zh-tw": "zh-TW", "zh": "zh-CN",
    "iw": "he", "no": "nb", "tl": "fil", "jw": "jv", "in": "id",
}

# Script-based detection using Unicode ranges (faster & more reliable than langdetect)
SCRIPT_MAP = [
    (r'[\u1780-\u17FF]', 'km'),        # Khmer
    (r'[\u0E00-\u0E7F]', 'th'),        # Thai
    (r'[\u0E80-\u0EFF]', 'lo'),        # Lao
    (r'[\u1000-\u109F]', 'my'),        # Myanmar
    (r'[\u1200-\u137F]', 'am'),        # Ethiopic → Amharic
    (r'[\u10A0-\u10FF]', 'ka'),        # Georgian
    (r'[\u0530-\u058F]', 'hy'),        # Armenian (no edge-tts, fallback en)
    (r'[\u0590-\u05FF]', 'he'),        # Hebrew
    (r'[\u0900-\u097F]', 'hi'),        # Devanagari → Hindi
    (r'[\u0980-\u09FF]', 'bn'),        # Bengali
    (r'[\u0A00-\u0A7F]', 'pa'),        # Gurmukhi → Punjabi
    (r'[\u0A80-\u0AFF]', 'gu'),        # Gujarati
    (r'[\u0B00-\u0B7F]', 'or'),        # Oriya
    (r'[\u0B80-\u0BFF]', 'ta'),        # Tamil
    (r'[\u0C00-\u0C7F]', 'te'),        # Telugu
    (r'[\u0C80-\u0CFF]', 'kn'),        # Kannada
    (r'[\u0D00-\u0D7F]', 'ml'),        # Malayalam
    (r'[\u0D80-\u0DFF]', 'si'),        # Sinhala
    (r'[\u0600-\u06FF]', 'ar'),        # Arabic script (ar/fa/ur/ps)
    (r'[\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]', 'ar'),  # Arabic extended
    (r'[\u0400-\u04FF]', 'ru'),        # Cyrillic → Russian (fallback)
    (r'[\u0370-\u03FF]', 'el'),        # Greek
    (r'[\u1800-\u18AF]', 'mn'),        # Mongolian script
    (r'[\uAC00-\uD7FF]', 'ko'),        # Korean Hangul
    (r'[\u3040-\u30FF]', 'ja'),        # Japanese Hiragana/Katakana
    (r'[\u4E00-\u9FFF\u3400-\u4DBF]', 'zh-CN'),  # CJK
]

GENDER_KEY = "voice_gender"

KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("👨 សំឡេងប្រុស"), KeyboardButton("👩 សំឡេងស្រី")]],
    resize_keyboard=True
)

def detect_language(text: str) -> str:
    # 1. Try script-based detection first (instant & reliable)
    for pattern, lang in SCRIPT_MAP:
        if re.search(pattern, text):
            # Refine Arabic-script languages using langdetect
            if lang == 'ar':
                try:
                    detected = langdetect_detect(text)
                    detected = NORMALIZE.get(detected, detected)
                    if detected in ('fa', 'ur', 'ps', 'ar'):
                        return detected
                except Exception:
                    pass
            # Refine Cyrillic languages using langdetect
            if lang == 'ru':
                try:
                    detected = langdetect_detect(text)
                    detected = NORMALIZE.get(detected, detected)
                    if detected in ('ru', 'uk', 'bg', 'sr', 'mk', 'kk', 'mn'):
                        return detected
                except Exception:
                    pass
            return lang

    # 2. For Latin-script text: use confidence threshold
    # Very short texts are unreliable — default to English
    stripped = text.strip()
    if len(stripped) < 15 or len(stripped.split()) < 3:
        return 'en'

    try:
        langs = detect_langs(text)
        if langs:
            top = langs[0]
            lang_code = NORMALIZE.get(top.lang, top.lang)
            # Accept detection only if confidence >= 0.70, else default English
            if top.prob >= 0.70:
                return lang_code
    except Exception:
        pass

    return 'en'

async def _start_ffmpeg():
    return await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-f", "mp3", "-i", "pipe:0",
        "-c:a", "libopus", "-b:a", "32k", "-ac", "1", "-ar", "16000", "-f", "ogg", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )

async def synthesize_to_bytes(text: str, voice: str, proc=None) -> BytesIO:
    if proc is None:
        proc = await _start_ffmpeg()

    communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            proc.stdin.write(chunk["data"])
    proc.stdin.close()

    stdout, _ = await proc.communicate()
    return BytesIO(stdout)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling update: {context.error}", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if GENDER_KEY not in context.user_data:
        context.user_data[GENDER_KEY] = "female"
    await update.message.reply_text(
        "🎙️ Text-to-Voice Bot\n\n"
        "ផ្ញើអត្ថបទណាមួយ ខ្ញុំបំប្លែងជាសំឡេងពិរោះ!\n"
        "🌐 គាំទ្រ 80+ ភាសា: ខ្មែរ, English, 中文, العربية, हिंदी...\n\n"
        "ជ្រើសសំឡេងប្រុស ឬស្រីដោយប្រើប៊ូតុងខាងក្រោម។",
        reply_markup=KEYBOARD
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👨 សំឡេងប្រុស":
        context.user_data[GENDER_KEY] = "male"
        await update.message.reply_text("✅ បានប្តូរទៅ 👨 សំឡេងប្រុស", reply_markup=KEYBOARD)
        return

    if text == "👩 សំឡេងស្រី":
        context.user_data[GENDER_KEY] = "female"
        await update.message.reply_text("✅ បានប្តូរទៅ 👩 សំឡេងស្រី", reply_markup=KEYBOARD)
        return

    text = text.strip()

    # Start ffmpeg process immediately (parallel with language detection)
    ffmpeg_task = asyncio.create_task(_start_ffmpeg())

    # Detect language while ffmpeg is starting up
    detected_lang = detect_language(text)
    gender = context.user_data.get(GENDER_KEY, "female")
    voice_map = MALE_VOICES if gender == "male" else FEMALE_VOICES

    voice = voice_map.get(detected_lang) or voice_map.get('en')
    lang_name = LANG_NAMES.get(detected_lang, detected_lang.upper())
    gender_label = "👨 ប្រុស" if gender == "male" else "👩 ស្រី"
    caption = f"🌐 {lang_name} | {gender_label}"

    cache_key = f"{voice}:{text}"
    cached_file_id = _cache_get(cache_key)

    logging.info(f"Detected: {detected_lang} | Chars: {len(text)} | Cache: {'HIT' if cached_file_id else 'MISS'}")

    quote = ReplyParameters(message_id=update.message.message_id)

    try:
        if cached_file_id:
            ffmpeg_task.cancel()
            await update.message.reply_voice(
                voice=cached_file_id,
                caption=caption,
                reply_markup=KEYBOARD,
                reply_parameters=quote
            )
        else:
            # Show recording indicator while synthesizing
            asyncio.create_task(
                context.bot.send_chat_action(
                    update.effective_chat.id,
                    constants.ChatAction.RECORD_VOICE
                )
            )
            proc = await ffmpeg_task
            audio_buf = await synthesize_to_bytes(text, voice, proc=proc)
            msg = await update.message.reply_voice(
                voice=audio_buf,
                caption=caption,
                reply_markup=KEYBOARD,
                reply_parameters=quote
            )
            _cache_set(cache_key, msg.voice.file_id)
    except Exception as e:
        logging.error(f"Error synthesizing voice: {e}")
        await update.message.reply_text(
            "⚠️ មានបញ្ហាក្នុងការបង្កើតសំឡេង។ សូមព្យាយាមម្តងទៀត។",
            reply_markup=KEYBOARD,
            reply_parameters=quote
        )

request = HTTPXRequest(
    connection_pool_size=32,
    read_timeout=60,
    write_timeout=60,
    connect_timeout=5,
    http_version="2",
)

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .request(request)
    .concurrent_updates(True)
    .build()
)
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)
app.run_polling(drop_pending_updates=True, timeout=30)
