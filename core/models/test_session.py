from sqlalchemy import (
    String,
    Boolean,
    Integer,
    BigInteger,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .pair import Pair


class TestSession(Base):
    pair_id: Mapped[int] = mapped_column(
        ForeignKey("pairs.id", ondelete="CASCADE"),
        index=True,
    )

    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    block: Mapped[int] = mapped_column(Integer)

    questions: Mapped[str] = mapped_column(String, nullable=True)
    answer: Mapped[str] = mapped_column(String, nullable=True)
    insight: Mapped[str] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=True)

    current_block: Mapped[int] = mapped_column(Integer, nullable=True)
    total_blocks: Mapped[int] = mapped_column(Integer, nullable=True)

    # Связь с парой
    pair: Mapped["Pair"] = relationship(
        "Pair",
        back_populates="test_sessions",
    )

    # ✅ ONE-TO-MANY
    subtestsessions: Mapped[List["SubTestSession"]] = relationship(
        "SubTestSession",
        back_populates="test_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SubTestSession(Base):
    # 👇 ВАЖНО — FK вместо secondary
    test_session_id: Mapped[int] = mapped_column(
        ForeignKey("testsessions.id", ondelete="CASCADE"),
        index=True,
    )

    questions: Mapped[str] = mapped_column(String, nullable=True)
    answer: Mapped[str] = mapped_column(String, nullable=True)
    insight: Mapped[str] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=True)

    current_block: Mapped[int] = mapped_column(Integer, nullable=True)
    total_blocks: Mapped[int] = mapped_column(Integer, nullable=True)

    # 👇 Обратная связь
    test_session: Mapped["TestSession"] = relationship(
        "TestSession",
        back_populates="subtestsessions",
    )
