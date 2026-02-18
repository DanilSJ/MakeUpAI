from sqlalchemy import String, Boolean, BigInteger, Integer, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base
import enum


class SubscriptionType(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class User(Base):
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Новые поля
    subscription: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType), default=SubscriptionType.FREE
    )
    ai_question: Mapped[int] = mapped_column(Integer, default=0)
    subscription_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    subscription_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ai_recharge_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
