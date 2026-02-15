from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper
from . import schemas
from . import crud

router = APIRouter()


@router.post("/", response_model=schemas.UserSchema)
async def create_user(
    user_in: schemas.RegisterSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.create_user(session=session, user_in=user_in)


@router.get("/{user_id}/", response_model=schemas.UserSchema)
async def get_user(
    telegram_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.get_user(session=session, telegram_id=telegram_id)


@router.patch("/{user_id}/update", response_model=schemas.UserSchema)
async def update_status_user(
    telegram_id: int,
    user_in: schemas.UpdateUserSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.update_status(
        session=session, telegram_id=telegram_id, user_in=user_in
    )
