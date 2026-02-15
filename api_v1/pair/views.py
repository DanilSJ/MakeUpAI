from fastapi import APIRouter, Depends
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper
from . import schemas
from . import crud

router = APIRouter()


@router.post("/create/", response_model=schemas.PairSchema)
async def create_pair(
    user_in: schemas.RegisterSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.create_pair(session=session, user_in=user_in)

@router.post("/join/", response_model=schemas.PairSchema)
async def join_pair(
    user_in: schemas.InviteSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.join_pair(session=session, user_in=user_in)
