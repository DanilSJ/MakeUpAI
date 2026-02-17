from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import TestSession
from .analyze import Analyze
from .base import Base


class Pair(Base):
    user_owner_telegram_id: Mapped[int] = mapped_column(BigInteger)
    user_pair_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String)

    test_sessions: Mapped[list["TestSession"]] = relationship(
        "TestSession", back_populates="pair", cascade="all, delete-orphan"
    )

    # Связь с Analyze (один ко многим) - необязательная
    analyzes: Mapped[list["Analyze"]] = relationship(
        "Analyze", back_populates="pair", cascade="all, delete-orphan"
    )
