from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🎁 Подобрать новые подарки", callback_data="new_selection")],
        [InlineKeyboardButton("📜 История подбора подарков", callback_data="history")],
        [InlineKeyboardButton("⭐️ Подписка на полный доступ", callback_data="subscription")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ Админ-меню", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu():
    keyboard = [
        [InlineKeyboardButton("📥 Загрузить базу", callback_data="upload_database")],
        [InlineKeyboardButton("📋 Просмотреть каталог", callback_data="view_catalog")],
        [InlineKeyboardButton("↩️ Вернуться в главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_recipient_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Подруге", callback_data="recipient_friend"),
            InlineKeyboardButton("Жене", callback_data="recipient_wife"),
            InlineKeyboardButton("Сестре", callback_data="recipient_sister")
        ],
        [
            InlineKeyboardButton("Маме", callback_data="recipient_mother"),
            InlineKeyboardButton("Мужу/Парню", callback_data="recipient_husband"),
            InlineKeyboardButton("Брату", callback_data="recipient_brother")
        ],
        [
            InlineKeyboardButton("Отцу", callback_data="recipient_father"),
            InlineKeyboardButton("Мужчина", callback_data="recipient_man"),
            InlineKeyboardButton("Женщина", callback_data="recipient_woman")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(callback_prefix: str):
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("Нет", callback_data=f"{callback_prefix}_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trend_scale_keyboard():
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"trend_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(str(i), callback_data=f"trend_{i}") for i in range(6, 11)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_gift_navigation_keyboard(current_index, total_categories, gifts):
    keyboard = []

    # Кнопки для подарков с их названиями
    for gift in gifts:
        keyboard.append([InlineKeyboardButton(gift.name, callback_data=f"gift_{gift.id}")])

    # Навигационные кнопки
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data="nav_prev"))
    if current_index < total_categories - 1:
        nav_buttons.append(InlineKeyboardButton("Следующая ➡️", callback_data="nav_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата в меню
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)


def get_history_keyboard(selections: list, page: int = 0, items_per_page: int = 5):
    keyboard = []

    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_page_selections = selections[start_idx:end_idx]

    for selection in current_page_selections:
        keyboard.append([
            InlineKeyboardButton(
                f"{selection.recipient_type} ({selection.created_at.strftime('%d.%m.%Y')})",
                callback_data=f"history_{selection.id}"
            )
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"history_page_{page - 1}"))
    if end_idx < len(selections):
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"history_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)
