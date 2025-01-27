from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from keyboards.inline import get_main_menu



async def handle_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "¯\\_(ツ)_/¯\n\n"
        "Пока тут пусто, но скоро мы начнем зарабатывать денежки!",
        reply_markup=get_main_menu()
    )


def register_subscription_handlers(application):
    application.add_handler(CallbackQueryHandler(handle_subscription, pattern="^subscription$"))
