from sqlalchemy import String, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)

    admin: Mapped[bool] = mapped_column(Boolean, default=False)
