import os
import asyncio
import logging
from http import HTTPStatus
from flask import Flask, request, make_response, Response
from asgiref.wsgi import WsgiToAsgi
import uvicorn

from telegram import Update
from bot import create_application  # 👈 your existing bot factory

# === Logging setup ===
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Environment config ===
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourdomain.com
PORT = int(os.getenv("PORT", 8000))

if not WEBHOOK_URL or not WEBHOOK_SECRET:
    raise RuntimeError("❌ Missing one of: WEBHOOK_URL, WEBHOOK_SECRET")

# === Flask + PTB setup ===
app = Flask(__name__)
application = create_application()  # builds PTB Application from your bot.py


# === Flask routes ===
@app.route("/", methods=["GET"])
async def index():
    """Simple health check"""
    return make_response("✅ Bot is running fine", HTTPStatus.OK)


@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
async def telegram_webhook():
    """Handle Telegram webhook POST updates"""
    try:
        update = Update.de_json(request.json, application.bot)
        await application.update_queue.put(update)
        logger.info(f"📩 Received update {update.update_id}")
    except Exception:
        logger.exception("Failed to process incoming update")
    return Response(status=HTTPStatus.OK)


# === Setup webhook ===
async def set_webhook():
    url = f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"
    await application.bot.set_webhook(url=url)
    logger.info(f"✅ Webhook successfully set to: {url}")


# === Main entrypoint ===
async def main():
    """Start PTB and Flask in the same async loop"""
    await set_webhook()

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(app),
            host="0.0.0.0",
            port=PORT,
            use_colors=False,
        )
    )

    async with application:
        await application.start()
        logger.info("🚀 PTB Application started")
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
