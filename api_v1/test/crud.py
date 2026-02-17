from fastapi import HTTPException
from sqlalchemy.exc import StatementError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from core.models import TestSession, Pair
from .schemas import RegisterSchema, SubmitSchema, TestSchema


async def start_test(session: AsyncSession, data_in: RegisterSchema) -> TestSession:
    pair_stmt = select(Pair).where(Pair.id == data_in.pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(
            status_code=404, detail=f"Pair with id {data_in.pair_id} does not exist"
        )

    if data_in.telegram_id not in [
        pair.user_owner_telegram_id,
        pair.user_pair_telegram_id,
    ]:
        raise HTTPException(status_code=403, detail="User is not a member of this pair")

    test_session = TestSession(**data_in.model_dump())
    session.add(test_session)

    try:
        await session.commit()
        await session.refresh(test_session)
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Database integrity error: {str(e)}"
        )
    except StatementError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Incorrect arguments")

    return test_session


async def submit_test(session: AsyncSession, data_in: SubmitSchema) -> TestSchema:
    stmt = select(TestSession).where(
        and_(
            TestSession.pair_id == data_in.pair_id,
            TestSession.telegram_id == data_in.telegram_id,
        )
    )

    result = await session.execute(stmt)
    test_session = result.scalars().first()

    if not test_session:
        raise HTTPException(
            status_code=404,
            detail="Test session not found or user does not have access",
        )

    try:
        update_data = data_in.model_dump(exclude_unset=True)

        update_data.pop("pair_id", None)
        update_data.pop("telegram_id", None)

        for field, value in update_data.items():
            setattr(test_session, field, value)

        await session.commit()
        await session.refresh(test_session)

        return TestSchema.model_validate(test_session)
    except StatementError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Incorrect arguments")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
