import random
from functools import wraps
from telegram import Update
from telegram.ext import ConversationHandler

def get_random_emoji():
    """"Return a random emoji character."""
    emoji_code = random.randint(0x1F600, 0x1F64F)
    return chr(emoji_code)


def group_only(func):
    """Decorator to restrict command usage to group chats only."""
    @wraps(func)
    async def wrapper(update: Update, context):
        chat = update.effective_chat
        if chat.type not in (chat.GROUP, chat.SUPERGROUP):
            await update.message.reply_text("Ця команда доступна лише в групах.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper
