import os
import asyncio
import logging
from flask import Flask, request
from bot import create_application
from telegram import Update

# === Logging setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# === Flask + PTB setup ===
app = Flask(__name__)
application = create_application()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourdomain.com


@app.route("/")
def index():
    logger.info("GET / called – health check OK")
    return "Bot is running."


@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    logger.info(f"Received update: {update_data.get('update_id', 'no_id')}")
    try:
        update = Update.de_json(update_data, application.bot)
        application.process_update(update)
        logger.info("Update processed successfully")
    except Exception:
        logger.exception("Failed to process update")
    return "ok"


async def set_webhook():
    url = f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"
    await application.bot.set_webhook(url=url)


def init_webhook():
    if WEBHOOK_URL and WEBHOOK_SECRET:
        asyncio.run(set_webhook())

# Run once on import (for waitress, gunicorn, etc.)
init_webhook()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)

