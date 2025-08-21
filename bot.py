import os
import random
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler
)
from flask import Flask
from threading import Thread
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# Web server setup
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# Tokens & DB
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["telegram_bot_db"]
groups_collection = db["tag_groups"]

# Random emoji
def get_random_emoji():
    emoji_code = random.randint(0x1F600, 0x1F64F)
    return chr(emoji_code)

# Start
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я бот для тегів з групами.")

# Only groups
def group_only(func):
    @wraps(func)
    async def wrapper(update: Update, context):
        chat = update.effective_chat
        if chat.type not in (chat.GROUP, chat.SUPERGROUP):
            await update.message.reply_text("Ця команда доступна лише в групах.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

# ===== STATES =====
JOIN, LEAVE, TAG, DELETE = range(4)

# ===== HELPER =====
def build_group_keyboard(chat_id):
    groups = list(groups_collection.find({"chat_id": chat_id}))
    keyboard = [[g["group_name"]] for g in groups]
    keyboard.append(["❌ Скасувати"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# ===== CREATE GROUP =====
@group_only
async def create_group(update: Update, context):
    if not context.args:
        await update.message.reply_text("Використання: /create_group <назва>")
        return ConversationHandler.END
    group_name = " ".join(context.args)
    chat_id = update.effective_chat.id

    # Check admin
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [a.user.id for a in admins]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("Тільки адміни можуть створювати групи.")
        return ConversationHandler.END

    count = groups_collection.count_documents({"chat_id": chat_id})
    if count >= 7:
        await update.message.reply_text("Досягнуто ліміту: максимум 7 груп у чаті.")
        return ConversationHandler.END

    if groups_collection.find_one({"chat_id": chat_id, "group_name": group_name}):
        await update.message.reply_text(f"Група '{group_name}' вже існує.")
    else:
        groups_collection.insert_one({"chat_id": chat_id, "group_name": group_name, "members": []})
        await update.message.reply_text(f"Група '{group_name}' створена.")
    return ConversationHandler.END

# ===== JOIN GROUP =====
@group_only
async def join_group_start(update: Update, context):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для приєднання:", reply_markup=build_group_keyboard(chat_id))
    return JOIN

async def join_group_choice(update: Update, context):
    group_name = update.message.text
    if group_name == "❌ Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = groups_collection.find_one({"chat_id": chat_id, "group_name": group_name})

    if not group:
        await update.message.reply_text("Група не знайдена.", reply_markup=ReplyKeyboardRemove())
    elif user_id in group["members"]:
        await update.message.reply_text("Ви вже у цій групі.", reply_markup=ReplyKeyboardRemove())
    else:
        groups_collection.update_one({"_id": group["_id"]}, {"$push": {"members": user_id}})
        await update.message.reply_text(f"Ви приєднались до групи '{group_name}'.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===== LEAVE GROUP =====
@group_only
async def leave_group_start(update: Update, context):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для виходу:", reply_markup=build_group_keyboard(chat_id))
    return LEAVE

async def leave_group_choice(update: Update, context):
    group_name = update.message.text
    if group_name == "❌ Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = groups_collection.find_one({"chat_id": chat_id, "group_name": group_name})

    if not group:
        await update.message.reply_text("Група не знайдена.", reply_markup=ReplyKeyboardRemove())
    elif user_id not in group["members"]:
        await update.message.reply_text("Вас немає у цій групі.", reply_markup=ReplyKeyboardRemove())
    else:
        groups_collection.update_one({"_id": group["_id"]}, {"$pull": {"members": user_id}})
        await update.message.reply_text(f"Ви вийшли з групи '{group_name}'.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===== TAG GROUP =====
@group_only
async def tag_group_start(update: Update, context):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для тегання:", reply_markup=build_group_keyboard(chat_id))
    return TAG

async def tag_group_choice(update: Update, context):
    group_name = update.message.text
    if group_name == "❌ Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = update.effective_chat.id
    group = groups_collection.find_one({"chat_id": chat_id, "group_name": group_name})

    if not group or not group["members"]:
        await update.message.reply_text("Група порожня або не існує.", reply_markup=ReplyKeyboardRemove())
    else:
        mentions = []
        for user_id in group["members"]:
            try:
                user = await context.bot.get_chat_member(chat_id, user_id)
                # if user.user.username: // Uncomment if you want to mention by username
                #     mentions.append(f"{get_random_emoji()} @{user.user.username}")
                # else:
                #     mentions.append(f"{get_random_emoji()} [{user.user.first_name}](tg://user?id={user_id})")
                if user:
                    mentions.append(f"[{get_random_emoji()}](tg://user?id={user.user.id})")
            except:
                continue
        if mentions:
            await update.message.reply_text(" ".join(mentions), parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("Немає учасників для тегання.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===== DELETE GROUP =====
@group_only
async def delete_group_start(update: Update, context):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для видалення:", reply_markup=build_group_keyboard(chat_id))
    return DELETE

async def delete_group_choice(update: Update, context):
    group_name = update.message.text
    if group_name == "❌ Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = update.effective_chat.id

    # Only admins
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [a.user.id for a in admins]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("Тільки адміни можуть видаляти групи.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    result = groups_collection.delete_one({"chat_id": chat_id, "group_name": group_name})
    if result.deleted_count:
        await update.message.reply_text(f"Групу '{group_name}' видалено ✅", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Група не знайдена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===== LIST GROUPS =====
@group_only
async def list_groups(update: Update, context):
    chat_id = update.effective_chat.id
    groups = groups_collection.find({"chat_id": chat_id})

    text = "Список груп:\n"
    found = False
    for group in groups:
        found = True
        text += f"- {group['group_name']} ({len(group['members'])} учасників)\n"
    if not found:
        text = "У цьому чаті немає груп."

    await update.message.reply_text(text)

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    # Simple commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('create_group', create_group))
    application.add_handler(CommandHandler('list_groups', list_groups))

    # Conversations
    join_conv = ConversationHandler(
        entry_points=[CommandHandler('join_group', join_group_start)],
        states={JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_group_choice)]},
        fallbacks=[],
    )
    leave_conv = ConversationHandler(
        entry_points=[CommandHandler('leave_group', leave_group_start)],
        states={LEAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, leave_group_choice)]},
        fallbacks=[],
    )
    tag_conv = ConversationHandler(
        entry_points=[CommandHandler('tag_group', tag_group_start)],
        states={TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, tag_group_choice)]},
        fallbacks=[],
    )
    delete_conv = ConversationHandler(
        entry_points=[CommandHandler('delete_group', delete_group_start)],
        states={DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_group_choice)]},
        fallbacks=[],
    )

    application.add_handler(join_conv)
    application.add_handler(leave_conv)
    application.add_handler(tag_conv)
    application.add_handler(delete_conv)

    # Run web server in thread
    web_thread = Thread(target=run_web_server)
    web_thread.start()

    application.run_polling()
