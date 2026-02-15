from sqlalchemy import String, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Pair(Base):
    user_owner_telegram_id: Mapped[int] = mapped_column(BigInteger)
    user_pair_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    invite_code: Mapped[str] = mapped_column(String, unique=True)
    status: Mapped[str] = mapped_column(String)
