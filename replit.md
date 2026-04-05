# Telegram TTS Bot

## Overview

Telegram Text-to-Speech bot built with Python. Converts user text messages into voice messages using Microsoft Edge TTS (`edge-tts`). Supports multilingual input including Khmer, Thai, Arabic, English, and many more.

## Stack

- **Language**: Python 3.11+
- **Bot Framework**: python-telegram-bot v22+
- **TTS Engine**: edge-tts (Microsoft Edge Neural voices)
- **Audio Processing**: ffmpeg (OGG Opus output)
- **Language Detection**: langdetect + Unicode script ranges

## Project Structure

```
├── bot.py              # Main bot logic (handlers, TTS synthesis, language detection)
├── api/
│   └── webhook.py      # Vercel serverless webhook handler
├── vercel.json         # Vercel deployment configuration
├── requirements.txt    # Python dependencies for Vercel
├── pyproject.toml      # Local/Replit dependencies (uv)
└── uv.lock             # Dependency lockfile
```

## Running Locally (Polling Mode)

The bot runs in polling mode when executed directly:

```bash
python bot.py
```

Requires `TELEGRAM_BOT_TOKEN` environment variable.

## Vercel Webhook Deployment

### 1. Deploy to Vercel

```bash
vercel deploy --prod
```

### 2. Set Environment Variable

In Vercel dashboard → Settings → Environment Variables:
- `TELEGRAM_BOT_TOKEN` = your bot token

Or use the Vercel CLI:
```bash
vercel env add TELEGRAM_BOT_TOKEN
```

### 3. Register Webhook with Telegram

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-domain>/api/webhook
```

### 4. Verify Webhook

```
https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

## Key Features

- Mixed-language text segmentation (Khmer + English in one message)
- Male/Female voice toggle via custom keyboard
- In-memory file_id caching (avoids re-uploading same audio)
- Parallel synthesis for multi-language segments
- Script-based language detection (faster than langdetect alone)

## Important Notes

- **ffmpeg** must be available in the deployment environment for audio conversion
- **user_data** (voice gender preference) is in-memory only — resets on cold starts in serverless
- Vercel hobby plan has 10s function timeout — very long texts may time out
