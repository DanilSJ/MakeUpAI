from fastapi import HTTPException
from sqlalchemy.engine import Result
from sqlalchemy.exc import StatementError
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


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def update_status(
    session: AsyncSession, telegram_id: int, user_in: schemas.UpdateUserSchema
) -> schemas.UserSchema:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user:
        try:
            for field, value in user_in.model_dump(exclude_unset=True).items():
                setattr(user, field, value)

            await session.commit()
            await session.refresh(user)

            return schemas.UserSchema.model_validate(user)
        except StatementError:
            raise HTTPException(status_code=400, detail="Incorrect arguments")

    raise HTTPException(status_code=404, detail="User does not exist")
