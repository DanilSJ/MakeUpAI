from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Pair(Base):
    user_owner_telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_pair_telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invite_code: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String)
