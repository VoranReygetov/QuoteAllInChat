import os
from flask import Flask, request
from bot import create_application

app = Flask(__name__)
application = create_application()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://yourdomain.com/webhook/<secret>

@app.route("/")
def index():
    return "Bot is running via webhook."

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    application.bot.set_webhook(f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}")
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
