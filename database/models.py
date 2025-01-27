from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    telegram_id = Column(BigInteger, primary_key=True)
    name = Column(String)
    username = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    selections = relationship("Selection", back_populates="user")

class Gift(Base):
    __tablename__ = 'gifts'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    link = Column(String(500))
    age_range = Column(String(50))
    price = Column(Float, nullable=False)
    city = Column(String(100))
    marketplace_available = Column(Boolean, default=True)
    trend_score = Column(Integer, default=5)
    consumable = Column(Boolean, default=False)
    creativity_score = Column(Integer, default=5)

    for_friend = Column(Boolean, default=False)
    for_wife = Column(Boolean, default=False)
    for_sister = Column(Boolean, default=False)
    for_mother = Column(Boolean, default=False)
    for_husband = Column(Boolean, default=False)
    for_brother = Column(Boolean, default=False)
    for_father = Column(Boolean, default=False)
    for_man = Column(Boolean, default=False)
    for_woman = Column(Boolean, default=False)

    image_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    selection_gifts = relationship("SelectionGift", back_populates="gift")
    selections = relationship(
        "Selection",
        secondary="selection_gifts",
        back_populates="gifts",
        overlaps="selection_gifts"
    )
    selection_gifts = relationship("SelectionGift", back_populates="gift")

class Selection(Base):
    __tablename__ = 'selections'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.telegram_id'))
    recipient_type = Column(String)
    age = Column(Integer)
    budget = Column(Float)
    marketplace = Column(Boolean)
    trend_score = Column(Integer)
    consumable = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="selections")
    selection_gifts = relationship("SelectionGift", back_populates="selection")
    gifts = relationship(
        "Gift",
        secondary="selection_gifts",
        back_populates="selections",
        overlaps="selection_gifts"
    )
    selection_gifts = relationship("SelectionGift", back_populates="selection")

class SelectionGift(Base):
    __tablename__ = 'selection_gifts'

    selection_id = Column(Integer, ForeignKey('selections.id'), primary_key=True)
    gift_id = Column(Integer, ForeignKey('gifts.id'), primary_key=True)
    category = Column(String(100))

    selection = relationship(
        "Selection",
        back_populates="selection_gifts",
        overlaps="gifts,selections"
    )
    gift = relationship(
        "Gift",
        back_populates="selection_gifts",
        overlaps="gifts,selections"
    )
