import secrets
import string

from fastapi import HTTPException
from sqlalchemy.engine import Result
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, BigInteger, exists
from core.models import Pair
from .schemas import PairSchema, RegisterSchema, InviteSchema

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 8


async def generate_unique_invite_code(session: AsyncSession) -> str:
    while True:
        invite_code = ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))

        query = select(exists().where(Pair.invite_code == invite_code))
        result = await session.execute(query)
        is_exists = result.scalar()

        if not is_exists:
            return invite_code


async def create_pair(session: AsyncSession, user_in: RegisterSchema) -> Pair:
    invite_code = await generate_unique_invite_code(session)

    user_in.invite_code = invite_code

    pair = Pair(**user_in.model_dump())
    session.add(pair)

    try:
        await session.commit()
        await session.refresh(pair)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating pair: {str(e)}")

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