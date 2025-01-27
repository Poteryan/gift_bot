from telegram import Bot
from database.database import get_session
from database.models import User
from typing import List, Union
import asyncio
import logging
from datetime import datetime


class NotificationManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    async def send_message(
            self,
            user_id: int,
            text: str,
            reply_markup: Union[None, any] = None,
            parse_mode: str = 'HTML'
    ) -> bool:
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            self.logger.error(f"Error sending message to {user_id}: {e}")
            return False

    async def broadcast(
            self,
            users: List[User],
            text: str,
            delay: float = 0.05
    ) -> dict:
        results = {
            'success': 0,
            'failed': 0,
            'total': len(users)
        }

        for user in users:
            success = await self.send_message(user.telegram_id, text)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
            await asyncio.sleep(delay)

        return results

    async def notify_admins(self, text: str, admin_ids: List[int]):
        for admin_id in admin_ids:
            await self.send_message(
                admin_id,
                f"🔔 Админ-уведомление:\n\n{text}"
            )

    async def send_daily_summary(self, admin_ids: List[int]):
        async with get_session() as session:
            today = datetime.now().date()

            # Получаем статистику за день
            stats = {
                'new_users': await session.scalar(
                    select(func.count(User.telegram_id)).where(
                        func.date(User.created_at) == today
                    )
                ),
                'selections_made': await session.scalar(
                    select(func.count(Selection.id)).where(
                        func.date(Selection.created_at) == today
                    )
                )
            }

            text = (
                "📊 Дневной отчет:\n\n"
                f"👥 Новых пользователей: {stats['new_users']}\n"
                f"🎁 Подборок сделано: {stats['selections_made']}"
            )

            await self.notify_admins(text, admin_ids)
