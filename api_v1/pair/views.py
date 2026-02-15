from fastapi import APIRouter, Depends
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

@router.post("/{pair_id}/", response_model=schemas.PairSchema)
async def get_pair(
    pair_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.get_pair(session=session, pair_id=pair_id)

@router.post("/{pair_id}/status/", response_model=schemas.PairSchema)
async def update_status_pair(
    pair_id: int,
    pair_in: schemas.UpdateStatusSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.update_status_pair(session=session, pair_id=pair_id, pair_in=pair_in)
