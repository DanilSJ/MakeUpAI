from sqlalchemy import Integer, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Analyze(Base):
    pair_id: Mapped[int] = mapped_column(ForeignKey("pairs.id", ondelete="CASCADE"))
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    block: Mapped[int] = mapped_column(Integer)

    analysis_json: Mapped[str] = mapped_column(Text, nullable=True)

    pair: Mapped["Pair"] = relationship("Pair", back_populates="analyzes")
