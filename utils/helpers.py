from typing import Union
import re
from datetime import datetime

def format_price(price: Union[int, float]) -> str:
    return f"{price:,.2f} ₽".replace(',', ' ')

def validate_phone(phone: str) -> bool:
    pattern = r'^\+?[1-9]\d{10,11}$'
    return bool(re.match(pattern, phone))

def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")

def get_age_range(age: int) -> tuple:
    if age <= 12:
        return (0, 12)
    elif age <= 18:
        return (13, 18)
    elif age <= 25:
        return (19, 25)
    elif age <= 35:
        return (26, 35)
    elif age <= 50:
        return (36, 50)
    else:
        return (51, 100)

def calculate_price_range(target_price: float) -> tuple:
    min_price = target_price * 0.75
    max_price = target_price * 1.25
    return (min_price, max_price)
