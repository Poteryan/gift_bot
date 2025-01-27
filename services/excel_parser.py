import numpy as np
import pandas as pd
from database.database import get_session, async_session
from database.models import Gift
from typing import List, Dict, Any
import logging
from sqlalchemy import delete

logger = logging.getLogger(__name__)


COLUMN_MAPPING = {
    'name': 'Название',
    'description': 'Описание',
    'category': 'Категория',
    'subcategory': 'Подкатегория',
    'link': 'Ссылка',
    'age_range': 'Возраст',
    'price': 'Стоимость',
    'city': 'Город',
    'marketplace_available': 'Маркетплейсы',
    'trend_score': 'Трендовый (10)/Традиционный (1)',
    'consumable': 'Подарок, который используется и исчезает',
    'creativity_score': 'Креативный (10)/Консервативный (1)',
    'for_friend': 'Подруге',
    'for_wife': 'Жене',
    'for_sister': 'Сестре',
    'for_mother': 'Маме',
    'for_husband': 'Мужу/Парню',
    'for_brother': 'Брату',
    'for_father': 'Отцу',
    'for_man': 'Мужчина',
    'for_woman': 'Женщина',
    'image_name': 'Фото'
}

class ExcelParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.columns = [
            'name', 'description', 'category', 'subcategory', 'link',
            'age_range', 'price', 'city', 'marketplace_available',
            'trend_score', 'consumable', 'creativity_score',
            'for_friend', 'for_wife', 'for_sister', 'for_mother',
            'for_husband', 'for_brother', 'for_father', 'for_man',
            'for_woman', 'image_name'
        ]

    def _validate_data(self, df: pd.DataFrame) -> bool:
        required_columns = set(self.columns)
        actual_columns = set(df.columns)

        if not required_columns.issubset(actual_columns):
            missing = required_columns - actual_columns
            logger.error(f"Отсутствуют обязательные колонки: {missing}")
            return False
        return True

    def _process_boolean_field(self, value: str) -> bool:
        return str(value).lower().strip() == 'да'

    def _process_row(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'name': str(row[0]),
            'description': str(row[1]),
            'category': str(row[2]),
            'subcategory': str(row[3]),
            'link': str(row[4]),
            'age_range': str(row[5]),
            'price': float(row[6]),
            'city': str(row[7]),
            'marketplace_available': self._process_boolean_field(row[8]),
            'trend_score': int(row[9]),
            'consumable': self._process_boolean_field(row[10]),
            'creativity_score': int(row[11]),
            'for_friend': self._process_boolean_field(row[12]),
            'for_wife': self._process_boolean_field(row[13]),
            'for_sister': self._process_boolean_field(row[14]),
            'for_mother': self._process_boolean_field(row[15]),
            'for_husband': self._process_boolean_field(row[16]),
            'for_brother': self._process_boolean_field(row[17]),
            'for_father': self._process_boolean_field(row[18]),
            'for_man': self._process_boolean_field(row[19]),
            'for_woman': self._process_boolean_field(row[20]),
            'image_name': str(row[21])
        }

    async def process_file(self) -> bool:
        try:
            df = pd.read_excel(self.file_path)

            if not self._validate_data(df):
                return False

            gifts_data = []
            for _, row in df.iterrows():
                try:
                    gift_data = self._process_row(row)
                    gifts_data.append(gift_data)
                except Exception as e:
                    logger.error(f"Ошибка обработки строки {row}: {str(e)}")
                    continue

            async with get_session() as session:
                # Очищаем текущую базу подарков
                await session.execute(delete(Gift))

                # Добавляем новые подарки
                for gift_data in gifts_data:
                    gift = Gift(**gift_data)
                    session.add(gift)

            logger.info(f"Успешно обработано {len(gifts_data)} подарков")
            return True

        except Exception as e:
            logger.error(f"Ошибка обработки файла: {str(e)}")
            return False


async def process_excel_file(file_path: str) -> bool:
    try:
        df = pd.read_excel(file_path)
        df = df.rename(columns={v: k for k, v in COLUMN_MAPPING.items()})

        # Преобразование boolean полей
        boolean_columns = ['marketplace_available', 'consumable', 'for_friend', 'for_wife',
                           'for_sister', 'for_mother', 'for_husband', 'for_brother',
                           'for_father', 'for_man', 'for_woman']

        for col in boolean_columns:
            df[col] = df[col].map({'Да': True, 'Нет': False, np.nan: False})

        # Преобразование числовых полей
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['trend_score'] = pd.to_numeric(df['trend_score'], errors='coerce')
        df['creativity_score'] = pd.to_numeric(df['creativity_score'], errors='coerce')

        async with async_session() as session:
            await session.execute(delete(Gift))

            for _, row in df.iterrows():
                gift = Gift(
                    name=str(row['name']),
                    description=str(row['description']),
                    category=str(row['category']),
                    subcategory=str(row.get('subcategory', '')),
                    link=str(row.get('link', '')),
                    age_range=str(row.get('age_range', '')),
                    price=float(row['price']) if pd.notna(row['price']) else 0,
                    city=str(row['city']),
                    marketplace_available=bool(row['marketplace_available']),
                    trend_score=int(row['trend_score']) if pd.notna(row['trend_score']) else 5,
                    consumable=bool(row['consumable']),
                    creativity_score=int(row['creativity_score']) if pd.notna(row['creativity_score']) else 5,
                    for_friend=bool(row['for_friend']),
                    for_wife=bool(row['for_wife']),
                    for_sister=bool(row['for_sister']),
                    for_mother=bool(row['for_mother']),
                    for_husband=bool(row['for_husband']),
                    for_brother=bool(row['for_brother']),
                    for_father=bool(row['for_father']),
                    for_man=bool(row['for_man']),
                    for_woman=bool(row['for_woman']),
                    image_name=str(row.get('image_name', ''))
                )
                session.add(gift)

            await session.commit()
            return True

    except Exception as e:
        logging.error(f"Ошибка обработки файла: {str(e)}")
        return False