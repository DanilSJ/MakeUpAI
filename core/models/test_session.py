from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class TestSession(Base):
    pair_id: Mapped[int] = mapped_column(Integer)
    block: Mapped[int] = mapped_column(Integer)
    questions: Mapped[list[str]] = mapped_column(String, nullable=True)
    insight: Mapped[str] = mapped_column(String, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=True)
    current_block: Mapped[int] = mapped_column(Integer, nullable=True)
    total_blocks: Mapped[int] = mapped_column(Integer, nullable=True)
