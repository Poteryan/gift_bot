import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///gift_bot.db')

# Настройки приложения
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
MAX_GIFTS_PER_CATEGORY = 2
ITEMS_PER_PAGE = 5

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')

# Создаем директории, если они не существуют
os.makedirs(IMAGES_DIR, exist_ok=True)
