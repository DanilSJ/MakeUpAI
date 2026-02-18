from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/{pair_id}/", response_model=schemas.PairSchema)
async def get_pair(
    pair_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.get_pair(session=session, pair_id=pair_id)


@router.patch("/{pair_id}/status/", response_model=schemas.PairSchema)
async def update_status_pair(
    pair_id: int,
    pair_in: schemas.UpdateStatusSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Обновляет статус пары и/или результаты тестов.
    Можно обновлять как одно поле, так и несколько одновременно.
    """
    return await crud.update_status_pair(
        session=session, pair_id=pair_id, pair_in=pair_in
    )


# Эндпоинт для обновления только теста владельца
@router.patch("/{pair_id}/owner-test/", response_model=schemas.PairSchema)
async def update_owner_test(
    pair_id: int,
    test_complete: bool,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Обновляет только поле user_owner_complete_test
    """
    update_data = schemas.UpdateStatusSchema(user_owner_complete_test=test_complete)
    return await crud.update_status_pair(
        session=session, pair_id=pair_id, pair_in=update_data
    )


# Эндпоинт для обновления только теста партнера
@router.patch("/{pair_id}/pair-test/", response_model=schemas.PairSchema)
async def update_pair_test(
    pair_id: int,
    test_complete: bool,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Обновляет только поле user_pair_complete_test
    """
    update_data = schemas.UpdateStatusSchema(user_pair_complete_test=test_complete)
    return await crud.update_status_pair(
        session=session, pair_id=pair_id, pair_in=update_data
    )


# Эндпоинт для обновления обоих тестов одновременно
@router.patch("/{pair_id}/both-tests/", response_model=schemas.PairSchema)
async def update_both_tests(
    pair_id: int,
    owner_test: bool,
    pair_test: bool,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Обновляет оба поля тестов одновременно
    """
    update_data = schemas.UpdateStatusSchema(
        user_owner_complete_test=owner_test, user_pair_complete_test=pair_test
    )
    return await crud.update_status_pair(
        session=session, pair_id=pair_id, pair_in=update_data
    )


@router.get("/by-user/{telegram_id}/", response_model=schemas.PairSchema)
async def get_pair_by_user_telegram_id(
    telegram_id: int,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Получить пару по user_owner_telegram_id или user_pair_telegram_id
    """
    pair = await crud.get_pair_by_user_telegram_id(
        session=session, telegram_id=telegram_id
    )
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found for this user")
    return pair


@router.get("/by-invite/{invite_code}/", response_model=schemas.PairSchema)
async def get_pair_by_invite_code(
    invite_code: str,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Получить пару по invite_code
    """
    pair = await crud.get_pair_by_invite_code(session=session, invite_code=invite_code)
    if not pair:
        raise HTTPException(
            status_code=404, detail="Pair not found for this invite code"
        )
    return pair
