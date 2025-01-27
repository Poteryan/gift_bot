from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from database.database import async_session
from database.models import User, Gift
from keyboards.inline import get_admin_menu, get_main_menu
from services.excel_parser import process_excel_file
import os
import logging
from telegram.error import BadRequest

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select, func


async def check_admin(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, user_id)
        return user and user.is_admin


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_admin(update.effective_user.id):
        await query.edit_message_text("У вас нет доступа к админ-панели.")
        return

    await query.edit_message_text(
        "Панель администратора:",
        reply_markup=get_admin_menu()
    )


async def upload_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await check_admin(update.effective_user.id):
        return

    await query.edit_message_text(
        "Отправьте Excel файл с базой подарков.\n"
        "Файл должен соответствовать заданной структуре."
    )


async def view_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # If there's no message to edit (was deleted), send a new one
    if not query.message:
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📋 Текущий каталог:",
            reply_markup=await get_catalog_keyboard(context)
        )
        return

    try:
        await query.edit_message_text(
            "📋 Текущий каталог:",
            reply_markup=await get_catalog_keyboard(context)
        )
    except BadRequest:
        # If we can't edit the message, send a new one
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📋 Текущий каталог:",
            reply_markup=await get_catalog_keyboard(context)
        )


async def get_catalog_keyboard(context):
    page = context.user_data.get('catalog_page', 0)
    items_per_page = 6

    async with async_session() as session:
        total_gifts = await session.execute(select(func.count(Gift.id)))
        total_count = total_gifts.scalar()

        gifts = await session.execute(
            select(Gift)
            .offset(page * items_per_page)
            .limit(items_per_page)
        )
        gifts = gifts.scalars().all()

        keyboard = []
        for gift in gifts:
            keyboard.append([InlineKeyboardButton(f"{gift.name} - {gift.price}₽",
                                                  callback_data=f"view_gift_{gift.id}")])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data="prev_catalog_page"))
        if (page + 1) * items_per_page < total_count:
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data="next_catalog_page"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        keyboard.append([InlineKeyboardButton("↩️ В админ-меню", callback_data="admin_menu")])

        return InlineKeyboardMarkup(keyboard)


async def view_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    gift_id = int(query.data.split('_')[2])

    async with async_session() as session:
        gift = await session.get(Gift, gift_id)

        text = f"🎁 {gift.name}\n\n"
        text += f"📝 {gift.description}\n\n"
        text += f"💰 {gift.price}₽"

        # Изменяем callback_data на соответствующий паттерн
        keyboard = [[InlineKeyboardButton("↩️ Назад к каталогу", callback_data="view_catalog")]]

        if gift.image_name:
            try:
                extensions = ['.jpg', '.jpeg', '.png']
                for ext in extensions:
                    photo_path = f"assets/images/{gift.image_name}{ext}"
                    try:
                        with open(photo_path, 'rb') as photo:
                            await query.message.reply_photo(
                                photo=photo,
                                caption=text,
                                reply_markup=InlineKeyboardMarkup(keyboard)
                            )
                            await query.message.delete()
                            break
                    except FileNotFoundError:
                        continue
            except Exception as e:
                logging.error(f"Ошибка при отправке фото: {e}")
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


async def handle_catalog_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "prev_catalog_page":
        context.user_data['catalog_page'] = max(0, context.user_data.get('catalog_page', 0) - 1)
    else:
        context.user_data['catalog_page'] = context.user_data.get('catalog_page', 0) + 1

    await view_catalog(update, context)


async def handle_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update.effective_user.id):
        return

    file = await context.bot.get_file(update.message.document)
    file_path = f"temp_{update.message.document.file_name}"

    try:
        await file.download_to_drive(file_path)
        await process_excel_file(file_path)
        await update.message.reply_text(
            "✅ База данных успешно обновлена!",
            reply_markup=get_admin_menu()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Произошла ошибка при обработке файла:\n{str(e)}"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != 583416877:
        return

    try:
        username = context.args[0].replace('@', '')  # Убираем @ если он есть
        async with async_session() as session:
            # Ищем пользователя по username в базе
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                user.is_admin = True
                await session.commit()
                await update.message.reply_text(f"✅ Пользователь @{username} назначен администратором")
            else:
                await update.message.reply_text("❌ Пользователь не найден в базе данных")
    except IndexError:
        await update.message.reply_text("ℹ️ Использование: /add @username")




async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    is_admin = await check_admin(update.effective_user.id)
    await query.edit_message_text(
        "Главное меню:",
        reply_markup=get_main_menu(is_admin=is_admin)
    )


def register_admin_handlers(application):
    application.add_handler(CallbackQueryHandler(admin_menu, pattern="^admin_menu$"))
    application.add_handler(CallbackQueryHandler(upload_database, pattern="^upload_database$"))
    application.add_handler(CallbackQueryHandler(view_catalog, pattern="^view_catalog$"))
    application.add_handler(CallbackQueryHandler(view_gift_details, pattern=r"^view_gift_\d+$"))
    application.add_handler(CallbackQueryHandler(handle_catalog_navigation, pattern="^(prev|next)_catalog_page$"))
    application.add_handler(CommandHandler("add", add_admin))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(
        MessageHandler(
            filters.Document.FileExtension("xlsx") | filters.Document.FileExtension("xls"),
            handle_excel_file
        )
    )
