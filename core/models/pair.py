from sqlalchemy import String, BigInteger, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .test_session import TestSession
    from .analyze import Analyze


class Pair(Base):
    user_owner_telegram_id: Mapped[int] = mapped_column(BigInteger)
    user_pair_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String)

    user_owner_complete_test: Mapped[bool] = mapped_column(Boolean, default=False)
    user_pair_complete_test: Mapped[bool] = mapped_column(Boolean, default=False)

    analyze_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    passport_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="pair",
        uselist=False,  # Явно указываем, что это one-to-one
        cascade="all, delete-orphan",
    )

    passport: Mapped[Optional["Passport"]] = relationship(
        "Passport",
        back_populates="pair",
        uselist=False,  # Явно указываем, что это one-to-one
        cascade="all, delete-orphan",
    )

    # ВАЖНО: поле называется test_sessions (с подчеркиванием)
    test_sessions: Mapped[list["TestSession"]] = relationship(
        "TestSession",
        back_populates="pair",  # В TestSession поле называется "pair"
        cascade="all, delete-orphan",
    )

    analyzes: Mapped[list["Analyze"]] = relationship(
        "Analyze", back_populates="pair", cascade="all, delete-orphan"
    )


class Profile(Base):
    """Профиль пользователя в паре (one-to-one с Pair)"""

    # Связь с парой (one-to-one)
    pair_id: Mapped[int] = mapped_column(
        ForeignKey("pairs.id", ondelete="CASCADE"),
        unique=True,  # Обеспечивает one-to-one
        index=True,
    )

    # Основная информация
    user_telegram_id: Mapped[int] = mapped_column(
        BigInteger
    )  # ID пользователя в телеграм
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    profile_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Отношение обратно к паре
    pair: Mapped["Pair"] = relationship(
        "Pair", back_populates="profile"  # Добавим это поле в Pair
    )


class Passport(Base):
    """паспорт пользователя в паре (one-to-one с Pair)"""

    # Связь с парой (one-to-one)
    pair_id: Mapped[int] = mapped_column(
        ForeignKey("pairs.id", ondelete="CASCADE"),
        unique=True,  # Обеспечивает one-to-one
        index=True,
    )

    passport_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Отношение обратно к паре
    pair: Mapped["Pair"] = relationship("Pair", back_populates="passport")
