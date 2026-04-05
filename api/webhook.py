import os
import sys
import json
import asyncio
import logging
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update
from bot import app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

_initialized = False


async def _process(update_data: dict):
    global _initialized
    if not _initialized:
        await app.initialize()
        _initialized = True
    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body)
            asyncio.run(_process(update_data))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            logging.error(f"Webhook error: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram TTS Bot webhook is active.")

    def log_message(self, format, *args):
        logging.info(f"[{self.address_string()}] {format % args}")
