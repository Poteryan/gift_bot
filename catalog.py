from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.database import async_session
from database.models import Gift


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        # Получаем все товары с пагинацией по 10 штук
        gifts = await session.execute(select(Gift).limit(10))
        gifts = gifts.scalars().all()

        keyboard = []
        for gift in gifts:
            keyboard.append([InlineKeyboardButton(
                f"{gift.name} - {gift.price}₽",
                callback_data=f"show_gift_{gift.id}"
            )])

        keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_menu")])

        await query.edit_message_text(
            "Каталог подарков:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    gift_id = int(query.data.split('_')[2])

    async with async_session() as session:
        gift = await session.get(Gift, gift_id)

        text = f"🎁 {gift.name}\n\n"
        text += f"💰 Цена: {gift.price}₽\n"
        text += f"📝 Описание: {gift.description}\n"
        text += f"🔗 Ссылка: {gift.link}\n"

        keyboard = [[InlineKeyboardButton("Назад к каталогу", callback_data="show_catalog")]]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )