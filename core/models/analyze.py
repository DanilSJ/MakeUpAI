from sqlalchemy import Integer, BigInteger, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Analyze(Base):
    pair_id: Mapped[int] = mapped_column(ForeignKey("pairs.id", ondelete="CASCADE"))
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    block: Mapped[int] = mapped_column(Integer)

    # JSON ответ от AI
    analysis_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    contradictions: Mapped[list] = mapped_column(JSON, nullable=True, default=[])

    # Обратная связь с Pair
    pair: Mapped["Pair"] = relationship("Pair", back_populates="analyzes")
