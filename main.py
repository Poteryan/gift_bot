import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from config.config import BOT_TOKEN
from handlers.admin import register_admin_handlers
from handlers.common import register_common_handlers
from handlers.gift_selection import register_gift_selection_handlers
from handlers.history import register_history_handlers
from handlers.subscription import register_subscription_handlers


def main():
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Создание приложения
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    register_common_handlers(app)
    register_gift_selection_handlers(app)
    register_admin_handlers(app)
    register_history_handlers(app)
    register_subscription_handlers(app)

    # Запуск бота
    app.run_polling(poll_interval=1)


if __name__ == '__main__':
    main()
