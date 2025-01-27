import logging

from telegram import Update
from telegram.ext import (ContextTypes, CommandHandler,
                          MessageHandler, filters, CallbackQueryHandler, ConversationHandler)
from database.database import async_session
from database.models import User
from keyboards.inline import get_main_menu
from telegram import KeyboardButton, ReplyKeyboardMarkup


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Start command received from user {update.effective_user.id}")
    try:
        async with async_session() as session:
            user = await session.get(User, update.effective_user.id)
            logging.info(f"User data: {user}")

            if not user:
                logging.info("New user - requesting phone number")
                keyboard = [[KeyboardButton("📱 Поделиться номером телефона", request_contact=True)]]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

                await update.message.reply_text(
                    "Добро пожаловать! Для начала работы поделитесь, пожалуйста, номером телефона.",
                    reply_markup=reply_markup
                )
                return

            logging.info("Existing user - showing main menu")
            await update.message.reply_text(
                f"С возвращением, {user.name}! Выберите действие:",
                reply_markup=get_main_menu(is_admin=user.is_admin)  # Передаём статус админа
            )
    except Exception as e:
        logging.error(f"Error in start_command: {e}")
        raise

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    username = update.effective_user.username

    async with async_session() as session:
        user = User(
            telegram_id=update.effective_user.id,
            phone=contact.phone_number,
            username=username  # Добавляем сохранение username
        )
        session.add(user)
        await session.commit()

    await update.message.reply_text(
        "Спасибо! Теперь введите ваше имя:"
    )


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user_id = update.effective_user.id

    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and not user.name:  # Проверяем, что имя ещё не установлено
            user.name = name
            context.user_data['user_name'] = name
            await session.commit()

            await update.message.reply_text(
                f"Отлично, {name}! Выберите действие:",
                reply_markup=get_main_menu()
            )
            # Сбрасываем состояние после завершения регистрации
            return ConversationHandler.END
        elif user and user.name:
            # Если имя уже установлено, игнорируем текстовые сообщения
            return
        else:
            await update.message.reply_text(
                "Пожалуйста, начните сначала с команды /start"
            )



def register_common_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    # Обрабатываем имя только при первой регистрации
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_name,
        block=True
    ), group=1)