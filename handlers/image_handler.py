from PIL import Image
import os
from config.config import IMAGES_DIR
import aiofiles
import logging
from typing import Optional


async def save_gift_image(image_data: bytes, image_name: str) -> Optional[str]:
    try:
        # Создаем имя файла
        filename = f"{image_name}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)

        # Сохраняем оригинальное изображение
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(image_data)

        # Оптимизируем изображение
        with Image.open(filepath) as img:
            # Изменяем размер, сохраняя пропорции
            max_size = (800, 800)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Сохраняем оптимизированное изображение
            img.save(filepath, 'JPEG', quality=85, optimize=True)

        return filename
    except Exception as e:
        logging.error(f"Ошибка при сохранении изображения: {e}")
        return None


async def delete_gift_image(image_name: str) -> bool:
    try:
        filepath = os.path.join(IMAGES_DIR, f"{image_name}.jpg")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        logging.error(f"Ошибка при удалении изображения: {e}")
        return False
