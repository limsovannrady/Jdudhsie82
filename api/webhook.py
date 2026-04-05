import os
import sys
import json
import asyncio
import logging
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update
from bot import create_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def _process(update_data: dict):
    application = create_app()
    await application.initialize()
    await application.start()
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
    finally:
        await application.stop()
        await application.shutdown()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body)
            asyncio.run(_process(update_data))
        except Exception as e:
            logging.error(f"Webhook error: {e}", exc_info=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram TTS Bot webhook is active.")

    def log_message(self, format, *args):
        logging.info(f"[{self.address_string()}] {format % args}")
