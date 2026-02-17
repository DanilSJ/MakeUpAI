from sqlalchemy import String, Boolean, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TestSession(Base):
    pair_id: Mapped[int] = mapped_column(ForeignKey("pairs.id", ondelete="CASCADE"))
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    block: Mapped[int] = mapped_column(Integer)
    questions: Mapped[str] = mapped_column(String, nullable=True)
    answer: Mapped[str] = mapped_column(String, nullable=True)
    insight: Mapped[str] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=True)
    current_block: Mapped[int] = mapped_column(Integer, nullable=True)
    total_blocks: Mapped[int] = mapped_column(Integer, nullable=True)

    pair: Mapped["Pair"] = relationship("Pair", back_populates="test_sessions")
