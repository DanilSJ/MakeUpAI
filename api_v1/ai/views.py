from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper
from . import schemas
from . import crud

router = APIRouter()


@router.post("/analyze/", response_model=schemas.AnalyzeResponseSchema)
async def start_analyze(
    pair_id: int,
    telegram_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.analyze_create(
        session=session,
        pair_id=pair_id,
        telegram_id=telegram_id,
    )


@router.post("/profile/", response_model=schemas.ProfileResponseSchema)
async def generate_profile(
    pair_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.generate_profile(
        session=session,
        pair_id=pair_id,
    )


@router.post("/passport/{pair_id}/", response_model=schemas.PassportResponseSchema)
async def generate_pair_passport(
    pair_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.generate_passport(session=session, pair_id=pair_id)
