from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from .models import Base, User, Gift, Selection, SelectionGift
from config.config import DATABASE_URL
import contextlib

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@contextlib.asynccontextmanager
async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user(telegram_id: int, phone: str = None, name: str = None):
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, phone=phone, name=name)
            session.add(user)
        else:
            if phone and not user.phone:
                user.phone = phone
            if name and not user.name:
                user.name = name

        return user

async def save_selection(user_id: int, recipient_type: str, selected_gifts: dict):
    async with get_session() as session:
        selection = Selection(user_id=user_id, recipient_type=recipient_type)
        session.add(selection)
        await session.flush()

        for category, gifts in selected_gifts.items():
            for gift in gifts:
                selection_gift = SelectionGift(
                    selection_id=selection.id,
                    gift_id=gift.id,
                    category=category
                )
                session.add(selection_gift)

async def get_gift_stats():
    async with get_session() as session:
        total_gifts = await session.scalar(select(func.count(Gift.id)))
        total_categories = await session.scalar(
            select(func.count(func.distinct(Gift.category)))
        )
        return {
            'total_gifts': total_gifts,
            'total_categories': total_categories
        }
