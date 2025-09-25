import os
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, MessageHandler, filters
)
from handlers import base, groups

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def create_application():
    app = Application.builder().token(TOKEN).build()

    # Simple commands
    app.add_handler(CommandHandler('start', base.start))
    app.add_handler(CommandHandler('create_group', groups.create_group))
    app.add_handler(CommandHandler('list_groups', groups.list_groups))

    # Conversations
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('join_group', groups.join_group_start)],
        states={groups.JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, groups.join_group_choice)]},
        fallbacks=[],
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('leave_group', groups.leave_group_start)],
        states={groups.LEAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, groups.leave_group_choice)]},
        fallbacks=[],
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('tag_group', groups.tag_group_start)],
        states={groups.TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, groups.tag_group_choice)]},
        fallbacks=[],
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler('delete_group', groups.delete_group_start)],
        states={groups.DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, groups.delete_group_choice)]},
        fallbacks=[],
    ))

    return app
