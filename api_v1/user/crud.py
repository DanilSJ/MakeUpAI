from fastapi import HTTPException
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import User
from . import schemas


async def create_user(session: AsyncSession, user_in: schemas.RegisterSchema) -> User:
    stmt = select(User).where(User.telegram_id == user_in.telegram_id)
    result: Result = await session.execute(stmt)

    if result.scalars().first():
        raise HTTPException(status_code=409, detail="User already exists")

    user = User(**user_in.model_dump())
    session.add(user)
    await session.commit()
    return user


async def get_user(session: AsyncSession, user_id) -> User | None:
    return await session.get(User, user_id)

