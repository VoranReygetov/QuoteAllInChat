from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from db import groups_collection
from utils import get_random_emoji, group_only

# STATES
JOIN, LEAVE, TAG, DELETE = range(4)

def build_group_keyboard(chat_id):
    groups = list(groups_collection.find({"chat_id": chat_id}))
    keyboard = [[g["group_name"]] for g in groups]
    keyboard.append(["❌ Скасувати"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# CREATE GROUP
@group_only
async def create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Використання: /create_group <назва>")
        return ConversationHandler.END
    group_name = " ".join(context.args)
    chat_id = update.effective_chat.id

    admins = await context.bot.get_chat_administrators(chat_id)
    admin_ids = [a.user.id for a in admins]
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("Тільки адміни можуть створювати групи.")
        return ConversationHandler.END

    if groups_collection.count_documents({"chat_id": chat_id}) >= 7:
        await update.message.reply_text("Досягнуто ліміту: максимум 7 груп у чаті.")
        return ConversationHandler.END

    if groups_collection.find_one({"chat_id": chat_id, "group_name": group_name}):
        await update.message.reply_text(f"Група '{group_name}' вже існує.")
    else:
        groups_collection.insert_one({"chat_id": chat_id, "group_name": group_name, "members": []})
        await update.message.reply_text(f"Група '{group_name}' створена.")
    return ConversationHandler.END

# JOIN
@group_only
async def join_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для приєднання:", reply_markup=build_group_keyboard(chat_id))
    return JOIN
    

async def join_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# LEAVE
@group_only
async def leave_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для виходу:", reply_markup=build_group_keyboard(chat_id))
    return LEAVE

async def leave_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# TAG
@group_only
async def tag_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для тегання:", reply_markup=build_group_keyboard(chat_id))
    return TAG

async def tag_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                mentions.append(f"[{get_random_emoji()}](tg://user?id={user.user.id})")
            except:
                continue
        if mentions:
            await update.message.reply_text(" ".join(mentions), parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("Немає учасників для тегання.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# DELETE
@group_only
async def delete_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if groups_collection.count_documents({"chat_id": chat_id}) == 0:
        await update.message.reply_text("У цьому чаті немає груп.")
        return ConversationHandler.END
    await update.message.reply_text("Оберіть групу для видалення:", reply_markup=build_group_keyboard(chat_id))
    return DELETE

async def delete_group_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.text
    if group_name == "❌ Скасувати":
        await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = update.effective_chat.id
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

# LIST
@group_only
async def list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
