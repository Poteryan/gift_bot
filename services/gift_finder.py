from database.database import get_session
from database.models import Gift
from sqlalchemy import select, and_, or_, func
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GiftFinder:
    def __init__(self, criteria: Dict[str, Any]):
        self.criteria = criteria
        self.filters = []

    def _add_price_filter(self):
        if self.criteria.get('budget', 0) > 0:
            budget = float(self.criteria['budget'])
            min_price = budget - 1000
            max_price = budget + 1000
            self.filters.append(Gift.price.between(min_price, max_price))

    def _add_age_filter(self):
        if 'age' in self.criteria:
            age = int(self.criteria['age'])
            self.filters.append(Gift.age_range.contains(str(age)))

    def _add_recipient_filter(self):
        recipient_mapping = {
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

        if recipient := self.criteria.get('recipient'):
            if recipient in recipient_mapping:
                self.filters.append(recipient_mapping[recipient] == True)

    def _add_marketplace_filter(self):
        if 'marketplace' in self.criteria:
            self.filters.append(Gift.marketplace_available == self.criteria['marketplace'])

    def _add_trend_filter(self):
        if 'trend_score' in self.criteria:
            trend_score = int(self.criteria['trend_score'])
            min_trend = max(1, trend_score - 1)
            max_trend = min(10, trend_score + 1)
            self.filters.append(Gift.trend_score.between(min_trend, max_trend))

    def _add_consumable_filter(self):
        if 'consumable' in self.criteria:
            self.filters.append(Gift.consumable == self.criteria['consumable'])

    async def find_gifts(self, limit_per_category: int = 2) -> Dict[str, List[Gift]]:
        self._add_price_filter()
        self._add_age_filter()
        self._add_recipient_filter()
        self._add_marketplace_filter()
        self._add_trend_filter()
        self._add_consumable_filter()

        async with get_session() as session:
            # Получаем все подходящие подарки
            query = select(Gift).where(and_(*self.filters))
            result = await session.execute(query)
            gifts = result.scalars().all()

            # Группируем по категориям
            categorized_gifts = {}
            for gift in gifts:
                if gift.category not in categorized_gifts:
                    categorized_gifts[gift.category] = []
                if len(categorized_gifts[gift.category]) < limit_per_category:
                    categorized_gifts[gift.category].append(gift)

            # Сортируем категории по количеству подарков и берем топ-3
            sorted_categories = dict(
                sorted(
                    categorized_gifts.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:3]
            )

            return sorted_categories


async def find_matching_gifts(criteria: Dict[str, Any]) -> Dict[str, List[Gift]]:
    finder = GiftFinder(criteria)
    return await finder.find_gifts()
