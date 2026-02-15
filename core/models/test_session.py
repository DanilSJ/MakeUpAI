from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class TestSession(Base):
    block: Mapped[int] = mapped_column(Integer)
    questions: Mapped[list[str]] = mapped_column(String)
    insight: Mapped[str] = mapped_column(String)
    success: Mapped[bool] = mapped_column(Boolean)
    current_block: Mapped[int] = mapped_column(Integer)
    total_blocks: Mapped[int] = mapped_column(Integer)
