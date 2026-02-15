from fastapi import HTTPException
from sqlalchemy.engine import Result
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, BigInteger
from core.models import Pair
from .schemas import PairSchema, RegisterSchema, InviteSchema


async def create_pair(session: AsyncSession, user_in: RegisterSchema) -> Pair:
    pair = Pair(**user_in.model_dump())
    session.add(pair)
    await session.commit()
    return pair

async def join_pair(session: AsyncSession, user_in: InviteSchema) -> PairSchema:
    stmt = select(Pair).where(Pair.invite_code == user_in.invite_code)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user:
        try:
            for field, value in user_in.model_dump(exclude_unset=True).items():
                setattr(user, field, value)

            await session.commit()
            await session.refresh(user)

            return PairSchema.model_validate(user)
        except StatementError:
            raise HTTPException(status_code=400, detail="Incorrect arguments")

    raise HTTPException(status_code=404, detail="Pier does not exist")