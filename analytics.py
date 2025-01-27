from database.database import get_session
from database.models import User, Selection, Gift
from sqlalchemy import func, select
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class Analytics:
    @staticmethod
    async def get_general_stats() -> Dict:
        async with get_session() as session:
            total_users = await session.scalar(select(func.count(User.telegram_id)))
            total_selections = await session.scalar(select(func.count(Selection.id)))
            total_gifts = await session.scalar(select(func.count(Gift.id)))

            return {
                'total_users': total_users,
                'total_selections': total_selections,
                'total_gifts': total_gifts
            }

    @staticmethod
    async def get_popular_categories() -> List[Tuple[str, int]]:
        async with get_session() as session:
            query = select(
                Gift.category,
                func.count(Selection.id).label('usage_count')
            ).join(Selection).group_by(Gift.category).order_by(func.count(Selection.id).desc())

            result = await session.execute(query)
            return result.all()

    @staticmethod
    async def get_daily_activity(days: int = 7) -> Dict[str, int]:
        async with get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = select(
                func.date(Selection.created_at),
                func.count(Selection.id)
            ).where(
                Selection.created_at >= start_date
            ).group_by(
                func.date(Selection.created_at)
            )

            result = await session.execute(query)
            return {str(date): count for date, count in result.all()}

    @staticmethod
    async def get_price_distribution() -> Dict[str, int]:
        async with get_session() as session:
            ranges = {
                '0-1000': (0, 1000),
                '1000-5000': (1000, 5000),
                '5000-10000': (5000, 10000),
                '10000+': (10000, float('inf'))
            }

            distribution = {}
            for range_name, (min_price, max_price) in ranges.items():
                count = await session.scalar(
                    select(func.count(Gift.id)).where(
                        Gift.price.between(min_price, max_price)
                    )
                )
                distribution[range_name] = count

            return distribution
