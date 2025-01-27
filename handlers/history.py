from asyncio.log import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from database.database import async_session
from database.models import Selection, SelectionGift, Gift
from keyboards.inline import get_main_menu, get_gift_navigation_keyboard
from sqlalchemy import select
import os

VIEWING_HISTORY, VIEWING_GIFTS, SHOWING_GIFT_DETAILS = range(3)

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    async with async_session() as session:
        stmt = select(Selection).where(
            Selection.user_id == update.effective_user.id
        ).order_by(Selection.created_at.desc())

        result = await session.execute(stmt)
        selections = result.scalars().all()

        if not selections:
            await query.edit_message_text(
                "У вас пока нет истории подборок подарков.",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

        keyboard = []
        for selection in selections:
            button_text = f"🎁 {selection.recipient_type} ({selection.created_at.strftime('%d.%m.%Y')})"
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"view_hist_{selection.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])

        await query.edit_message_text(
            "📜 Выберите подборку для просмотра:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return VIEWING_HISTORY

async def view_historical_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selection_id = int(query.data.split('_')[2])

    async with async_session() as session:
        stmt = select(Gift).join(SelectionGift).where(
            SelectionGift.selection_id == selection_id
        )
        result = await session.execute(stmt)
        gifts = result.scalars().all()

        gifts_by_category = {}
        for gift in gifts:
            category = gift.category if gift.category else "Без категории"
            if category not in gifts_by_category:
                gifts_by_category[category] = []
            gifts_by_category[category].append(gift)

        context.user_data['current_gifts'] = gifts_by_category
        context.user_data['current_category_index'] = 0

        await show_category_gifts(update, context)
        return VIEWING_GIFTS

async def show_category_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if isinstance(update, Update) else update
    message = query.message

    gifts_by_category = context.user_data.get('current_gifts', {})
    current_index = context.user_data.get('current_category_index', 0)
    categories = list(gifts_by_category.keys())

    if query.data and query.data.startswith('nav_'):
        if query.data == "nav_prev":
            current_index = max(0, current_index - 1)
        elif query.data == "nav_next":
            current_index = min(len(categories) - 1, current_index + 1)

    context.user_data['current_category_index'] = current_index
    current_category = categories[current_index]
    gifts = gifts_by_category[current_category]

    category_count = len(categories)
    category_word = "категории" if category_count in [2, 3, 4] else "категориях" if category_count >= 5 else "категории"

    text = f"Мы подобрали для вас подарки в {category_count} {category_word}.\n\n"
    text += f"Сейчас: {current_category}\n\n"

    for i, gift in enumerate(gifts, 1):
        text += f"{i}) [{gift.name}]({gift.link})\n"

    text += f"\nСтраница {current_index + 1} из {len(categories)}"

    keyboard = get_gift_navigation_keyboard(current_index, len(categories), gifts)

    try:
        image_path = None
        for gift in gifts:
            for ext in ['.png', '.jpg', '.jpeg']:
                temp_path = f"assets/images/{gift.image_name}{ext}"
                if os.path.exists(temp_path):
                    image_path = temp_path
                    break
            if image_path:
                break

        if image_path:
            with open(image_path, 'rb') as photo:
                await message.edit_media(
                    media=InputMediaPhoto(
                        media=photo,
                        caption=text,
                        parse_mode='Markdown'
                    ),
                    reply_markup=keyboard
                )
        else:
            await message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error showing category gifts: {e}")
        await message.edit_text(
            "Произошла ошибка при отображении подарков. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "nav_back":
        await show_category_gifts(update, context)
        return VIEWING_GIFTS

    gift_id = int(query.data.split('_')[1])

    async with async_session() as session:
        gift = await session.get(Gift, gift_id)
        if not gift:
            await query.message.edit_text(
                "Подарок не найден.",
                reply_markup=get_main_menu()
            )
            return ConversationHandler.END

        text = (
            f"*{gift.name}*\n"
            f"💰 Цена: {gift.price:,.2f} ₽\n\n"
            f"_{gift.description[:700] + '...' if len(gift.description) > 700 else gift.description}_\n\n"
            f"[Подробнее]({gift.link})"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="nav_back")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ])

        try:
            image_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                temp_path = f"assets/images/{gift.image_name}{ext}"
                if os.path.exists(temp_path):
                    image_path = temp_path
                    break

            if image_path:
                with open(image_path, 'rb') as photo:
                    await query.message.edit_media(
                        media=InputMediaPhoto(
                            media=photo,
                            caption=text,
                            parse_mode='Markdown'
                        ),
                        reply_markup=keyboard
                    )
            else:
                await query.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
        except Exception as e:
            logger.error(f"Error showing gift details: {e}")
            short_text = (
                f"*{gift.name}*\n"
                f"💰 Цена: {gift.price:,.2f} ₽\n\n"
                f"[Подробнее]({gift.link})"
            )
            await query.message.edit_text(
                short_text,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )

    return SHOWING_GIFT_DETAILS


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # Try to edit the message text first
        await query.message.edit_text(
            "Главное меню",
            reply_markup=get_main_menu()
        )
    except Exception:
        # If editing text fails, try to edit media message
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(
                    media=open("assets/images/main_menu.jpg", 'rb'),
                    caption="Главное меню"
                ),
                reply_markup=get_main_menu()
            )
        except Exception:
            # If both fail, send a new message
            await query.message.reply_text(
                "Главное меню",
                reply_markup=get_main_menu()
            )

    return ConversationHandler.END

def register_history_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(show_history, pattern="^history$")],
        states={
            VIEWING_HISTORY: [
                CallbackQueryHandler(view_historical_gifts, pattern=r"^view_hist_\d+$")
            ],
            VIEWING_GIFTS: [
                CallbackQueryHandler(show_category_gifts, pattern="^nav_"),
                CallbackQueryHandler(show_gift_details, pattern="^gift_")
            ],
            SHOWING_GIFT_DETAILS: [
                CallbackQueryHandler(show_category_gifts, pattern="^nav_back$"),
                CallbackQueryHandler(show_history, pattern="^history$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")
        ],
        name="history_conversation",
        per_message=True
    )

    application.add_handler(conv_handler)
