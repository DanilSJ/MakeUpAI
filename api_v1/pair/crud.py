from fastapi import HTTPException
from sqlalchemy.engine import Result
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, BigInteger
from core.models import Pair
from . import schemas


async def create_pair(session: AsyncSession, user_in: schemas.RegisterSchema) -> Pair:
    pair = Pair(**user_in.model_dump())
    session.add(pair)
    await session.commit()
    return pair