from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import StatementError
from datetime import datetime
from core.models import User
from . import schemas


async def create_user(session: AsyncSession, user_in: schemas.RegisterSchema) -> User:
    stmt = select(User).where(User.telegram_id == user_in.telegram_id)
    result = await session.execute(stmt)

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


# --- Новая функция для обновления подписки ---
async def update_subscription(
    session: AsyncSession,
    telegram_id: int,
    data: schemas.UpdateSubscriptionSchema,
):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        user.subscription = data.subscription
        user.subscription_start = datetime.utcnow()
        user.subscription_end = data.subscription_end

        await session.commit()
        await session.refresh(user)

        return user
    except StatementError:
        raise HTTPException(status_code=400, detail="Invalid data")


async def update_ai_question(
    session: AsyncSession,
    telegram_id: int,
    data: schemas.UpdateAIQuestionSchema,
):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.ai_question = data.ai_question

    await session.commit()
    await session.refresh(user)

    return user


async def update_ai_recharge_time(
    session: AsyncSession,
    telegram_id: int,
    data: schemas.UpdateAIRechargeTimeSchema,
):
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.ai_recharge_time = data.ai_recharge_time

    await session.commit()
    await session.refresh(user)

    return user
