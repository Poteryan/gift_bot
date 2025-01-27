import telegram
from telegram import InputMediaPhoto
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from database.database import async_session
from database.models import Gift, Selection, SelectionGift
from keyboards.inline import (
    get_recipient_keyboard,
    get_yes_no_keyboard,
    get_trend_scale_keyboard,
    get_gift_navigation_keyboard,
    get_main_menu
)
from sqlalchemy import select, func
import os
from PIL import Image

# Состояния разговора
(
    AGE,
    RECIPIENT,
    BUDGET,
    MARKETPLACE,
    TREND,
    CONSUMABLE,
    SHOWING_RESULTS
) = range(7)


async def show_gift_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('nav_back'):
        await show_category_gifts(update, context)
        return SHOWING_RESULTS

    gift_id = int(query.data.split('_')[1])

    async with async_session() as session:
        gift = await session.get(Gift, gift_id)

        # Сокращаем описание, если оно слишком длинное
        description = gift.description
        if len(description) > 700:
            description = description[:697] + "..."

        # Формируем более короткий текст
        text = (
            f"*{gift.name}*\n"
            f"💰 Цена: {gift.price:,.2f} ₽\n\n"
            f"_{description}_\n\n"
            f"[Подробнее]({gift.link})"
        )

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="nav_back")],
            [InlineKeyboardButton("🏠 В меню", callback_data="main_menu")]
        ]

        image_path = None
        for ext in ['.png', '.jpg', '.jpeg']:
            temp_path = f"assets/images/{gift.image_name}{ext}"
            if os.path.exists(temp_path):
                image_path = temp_path
                break

        try:
            if image_path:
                await query.message.edit_media(
                    media=InputMediaPhoto(
                        media=open(image_path, 'rb'),
                        caption=text,
                        parse_mode='Markdown'
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
        except telegram.error.BadRequest as e:
            # Если всё ещё слишком длинное, отправляем совсем короткую версию
            short_text = (
                f"*{gift.name}*\n"
                f"💰 Цена: {gift.price:,.2f} ₽\n\n"
                f"[Подробнее]({gift.link})"
            )
            if image_path:
                await query.message.edit_media(
                    media=InputMediaPhoto(
                        media=open(image_path, 'rb'),
                        caption=short_text,
                        parse_mode='Markdown'
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.message.edit_text(
                    short_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )

    return SHOWING_RESULTS


async def cancel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Delete the current message with photo
    await query.message.delete()

    # Send a new message with main menu
    await query.message.reply_text(
        f"{context.user_data['selection']['user_name']}, вы в главном меню. Выберите действие:",
        reply_markup=get_main_menu()
    )

    return ConversationHandler.END


async def start_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Initialize selection data with user's name
    context.user_data['selection'] = {
        'user_name': update.effective_user.first_name
    }

    await query.edit_message_text(
        "Укажите возраст человека, которому подбираем подарок (от 0 до 100):"
    )
    return AGE


async def process_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if not 0 <= age <= 100:
            await update.message.edit_text("Пожалуйста, введите корректный возраст (от 0 до 100):")
            return AGE

        context.user_data['selection'] = {
            'age': age,
            'user_name': context.user_data.get('user_name', update.effective_user.first_name)
        }

        # Сохраняем ID сообщения для последующего редактирования
        context.user_data['message_id'] = update.message.message_id

        await update.message.edit_text(
            "Кому подбираем подарок?",
            reply_markup=get_recipient_keyboard()
        )
        return RECIPIENT

    except ValueError:
        await update.message.edit_text("Пожалуйста, введите число от 0 до 100:")
        return AGE


async def process_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if not 0 <= age <= 100:
            await update.message.reply_text("Пожалуйста, введите корректный возраст (от 0 до 100):")
            return AGE

        # Сохраняем возраст в контексте
        context.user_data['selection'] = {
            'age': age,
            'user_name': context.user_data.get('user_name', update.effective_user.first_name)
        }

        # Переходим к выбору получателя подарка
        await update.message.reply_text(
            "Кому подбираем подарок?",
            reply_markup=get_recipient_keyboard()
        )
        return RECIPIENT

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число от 0 до 100:")
        return AGE


async def process_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    recipient = query.data.replace("recipient_", "")
    context.user_data['selection']['recipient'] = recipient

    await query.edit_message_text(
        "Какой у вас бюджет для подарка? Если бюджет не важен - напишите 0:"
    )
    return BUDGET


async def process_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        budget = float(update.message.text)
        if budget < 0:
            await update.message.reply_text("Пожалуйста, введите положительное число или 0:")
            return BUDGET

        context.user_data['selection']['budget'] = budget

        await update.message.reply_text(
            "Рассматриваем ли мы подарки с маркетплейсов?",
            reply_markup=get_yes_no_keyboard("marketplace")
        )
        return MARKETPLACE

    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную сумму:")
        return BUDGET


async def process_marketplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    marketplace = query.data.split('_')[1] == 'yes'
    context.user_data['selection']['marketplace'] = marketplace

    await query.edit_message_text(
        "Насколько трендовый или традиционный подарок должен быть?\n"
        "Оцените по шкале от 1 до 10, где:\n"
        "1 - традиционный\n"
        "10 - трендовый",
        reply_markup=get_trend_scale_keyboard()
    )
    return TREND


async def process_trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    trend_score = int(query.data.split('_')[1])
    context.user_data['selection']['trend_score'] = trend_score

    await query.edit_message_text(
        "Вы хотите подарить разовый подарок? (подарки, которые доставляют удовольствие, "
        "но при этом не остаются в доме)",
        reply_markup=get_yes_no_keyboard("consumable")
    )
    return CONSUMABLE


async def find_matching_gifts(selection_data):
    # Определяем словарь фильтров получателей
    recipient_filters = {
        'friend': Gift.for_friend,
        'wife': Gift.for_wife,
        'sister': Gift.for_sister,
        'mother': Gift.for_mother,
        'husband': Gift.for_husband,
        'brother': Gift.for_brother,
        'father': Gift.for_father,
        'man': Gift.for_man,
        'woman': Gift.for_woman
    }

    async with async_session() as session:
        base_query = select(Gift)
        filters = []

        # Фильтр получателя
        if selection_data['recipient'] in recipient_filters:
            filters.append(recipient_filters[selection_data['recipient']] == True)

        # Остальные фильтры
        filters.append(Gift.marketplace_available == selection_data['marketplace'])
        filters.append(Gift.consumable == selection_data['consumable'])

        # Применяем базовые фильтры
        base_query = base_query.filter(*filters)

        # Пробуем найти подарки с точным соответствием trend_score
        trend_query = base_query.filter(Gift.trend_score == selection_data['trend_score'])
        results = await session.execute(trend_query)
        gifts = results.scalars().all()

        # Если подарков не найдено, расширяем диапазон поиска
        if not gifts:
            trend_query = base_query.filter(
                Gift.trend_score.between(
                    selection_data['trend_score'] - 2,
                    selection_data['trend_score'] + 2
                )
            )
            results = await session.execute(trend_query)
            gifts = results.scalars().all()

        print("Debug: Selection data:", selection_data)
        print("Debug: SQL Query:", str(trend_query))
        print("Debug: Found gifts:", len(gifts))

        # Группировка результатов
        categorized_gifts = {}
        for gift in gifts:
            if gift.category not in categorized_gifts:
                categorized_gifts[gift.category] = []
            if len(categorized_gifts[gift.category]) < 2:
                categorized_gifts[gift.category].append(gift)

        return dict(sorted(categorized_gifts.items())[:3])


async def process_consumable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    consumable = query.data.split('_')[1] == 'yes'
    context.user_data['selection']['consumable'] = consumable

    # Поиск подходящих подарков
    gifts_by_category = await find_matching_gifts(context.user_data['selection'])

    if not gifts_by_category:
        await query.edit_message_text(
            f"К сожалению, {context.user_data['selection']['user_name']}, подходящих подарков не найдено. Попробуйте изменить критерии поиска.",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END

    # Сохраняем подборку в базу данных
    async with async_session() as session:
        selection = Selection(
            user_id=update.effective_user.id,
            recipient_type=context.user_data['selection']['recipient'],
            age=context.user_data['selection']['age'],
            budget=context.user_data['selection']['budget'],
            marketplace=context.user_data['selection']['marketplace'],
            trend_score=context.user_data['selection']['trend_score'],
            consumable=consumable
        )
        session.add(selection)
        await session.flush()

        # Сохраняем связи с подарками
        for category_gifts in gifts_by_category.values():
            for gift in category_gifts:
                selection_gift = SelectionGift(
                    selection_id=selection.id,
                    gift_id=gift.id
                )
                session.add(selection_gift)

        await session.commit()

    context.user_data['current_gifts'] = gifts_by_category
    context.user_data['current_category_index'] = 0

    # Показываем первую категорию
    await show_category_gifts(query, context)
    return SHOWING_RESULTS


async def show_category_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update):
        query = update.callback_query
        await query.answer()
    else:
        query = update

    gifts_by_category = context.user_data['current_gifts']
    current_index = context.user_data['current_category_index']

    if hasattr(query, 'data') and query.data:
        if query.data == "nav_prev":
            current_index = max(0, current_index - 1)
        elif query.data == "nav_next":
            current_index = min(len(gifts_by_category) - 1, current_index + 1)

    context.user_data['current_category_index'] = current_index

    categories = list(gifts_by_category.keys())
    current_category = categories[current_index]
    gifts = gifts_by_category[current_category]

    text = f"Отлично! Мы подобрали для вас подарки в {len(gifts_by_category)} категориях.\n\n"
    text += f"Сейчас: {current_category}\n\n"

    for i, gift in enumerate(gifts, 1):
        text += f"{i}) [{gift.name}]({gift.link})\n"

    media_group = []
    for gift in gifts:
        for ext in ['.png', '.jpg', '.jpeg']:
            image_path = f"assets/images/{gift.image_name}{ext}"
            if os.path.exists(image_path):
                media_group.append(open(image_path, 'rb'))
                break

    try:
        if media_group:
            await query.message.edit_media(
                media=InputMediaPhoto(
                    media=media_group[0],
                    caption=text,
                    parse_mode='Markdown'
                ),
                reply_markup=get_gift_navigation_keyboard(current_index, len(categories), gifts)
            )
        else:
            await query.edit_message_text(
                text,
                reply_markup=get_gift_navigation_keyboard(current_index, len(categories), gifts),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
    finally:
        for media in media_group:
            media.close()





def register_gift_selection_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_selection, pattern="^new_selection$")],
        states={
            AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_age)
            ],
            RECIPIENT: [
                CallbackQueryHandler(process_recipient, pattern="^recipient_")
            ],
            BUDGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_budget)
            ],
            MARKETPLACE: [
                CallbackQueryHandler(process_marketplace, pattern="^marketplace_")
            ],
            TREND: [
                CallbackQueryHandler(process_trend, pattern="^trend_")
            ],
            CONSUMABLE: [
                CallbackQueryHandler(process_consumable, pattern="^consumable_")
            ],
            SHOWING_RESULTS: [
                CallbackQueryHandler(show_category_gifts, pattern="^nav_"),
                CallbackQueryHandler(show_gift_details, pattern="^gift_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_selection, pattern="^cancel$"),
            CallbackQueryHandler(cancel_selection, pattern="^main_menu$")
        ],
        per_message=False,
        name="gift_selection"
    )

    application.add_handler(conv_handler)
