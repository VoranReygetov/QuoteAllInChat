import random
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telegram import Update
from telegram.ext import Application, CommandHandler

# Ваш токен
TOKEN = '7271802754:AAERCOjt5jnA1lGxEoFVkMQzxedlMKLdgH4'

# Create a new client and connect to the server
uri = "mongodb+srv://voran009:bXRdnafc5uspejem@qouteallchats.o3dy4.mongodb.net/?retryWrites=true&w=majority&appName=QouteAllChats"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["telegram_bot_db"]
optout_collection = db["optout_users"]


# Функція для вибору випадкового емодзі через юнікод
def get_random_emoji():
    # Діапазон юнікодів для емодзі (обличчя)
    emoji_code = random.randint(0x1F400, 0x1F4D3)  # Випадковий код у діапазоні
    return chr(emoji_code)  # Перетворюємо код на символ

async def start(update: Update, context):
    await update.message.reply_text("Hello! I'm a bot.")

# Функція для виключення з тегання
async def optout(update: Update, context):
    user_id = update.effective_user.id
    # Перевіряємо, чи користувач вже є у базі
    if optout_collection.find_one({"user_id": user_id}):
        await update.message.reply_text("Ви вже виключені з тегання.")
    else:
        optout_collection.insert_one({"user_id": user_id})
        await update.message.reply_text("Вас виключено з тегання.")

# Функція для повернення у список тегання
async def optin(update: Update, context):
    user_id = update.effective_user.id
    # Перевіряємо, чи користувач у базі та видаляємо його
    if optout_collection.find_one({"user_id": user_id}):
        optout_collection.delete_one({"user_id": user_id})
        await update.message.reply_text("Вас додано до списку тегання.")
    else:
        await update.message.reply_text("Вас не було виключено з тегання.")

# Функція для тегання всіх (за винятком тих, хто виключив себе)
async def tag_all(update: Update, context):
    chat = update.effective_chat
    members = await context.bot.get_chat_administrators(chat.id)

    # Отримуємо список користувачів, які виключили себе з тегання
    optout_users = optout_collection.find({})
    optout_user_ids = [user["user_id"] for user in optout_users]

    # Генеруємо випадкові емодзі для кожного користувача і перевіряємо, чи він у списку виключених
    user_tags = [
        f"[{get_random_emoji()}](tg://user?id={member.user.id})"
        for member in members
        if member.user.username and member.user.id not in optout_user_ids
    ]

    if user_tags:
        await update.message.reply_text(" ".join(user_tags), parse_mode='MarkdownV2')
    else:
        await update.message.reply_text("Немає користувачів для тегання.")

if __name__ == '__main__':
    # Створюємо Application
    application = Application.builder().token(TOKEN).build()

    # Створюємо команди
    start_handler = CommandHandler('start', start)
    tag_all_handler = CommandHandler('all', tag_all)
    optout_handler = CommandHandler('optout', optout)
    optin_handler = CommandHandler('optin', optin)

    # Додаємо команди в обробник
    application.add_handler(start_handler)
    application.add_handler(tag_all_handler)
    application.add_handler(optout_handler)
    application.add_handler(optin_handler)

    # Запускаємо бота
    application.run_polling()
