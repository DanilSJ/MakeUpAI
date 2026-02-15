from fastapi import HTTPException
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.models import TestSession
from .schemas import RegisterSchema, SubmitSchema, TestSchema


async def start_test(session: AsyncSession, data_in: RegisterSchema) -> TestSession:
    pair = TestSession(**data_in.model_dump())
    session.add(pair)

    await session.commit()
    await session.refresh(pair)

    return pair


async def submit_test(session: AsyncSession, data_in: SubmitSchema) -> TestSchema:
    stmt = select(TestSession).where(TestSession.id == data_in.session_id)
    result = await session.execute(stmt)
    data = result.scalars().first()

    if data:
        try:
            # TODO: тут запрос к deepseek на insight
            # response = await deepseek(prompt)
            # data_in.insight = response

            for field, value in data_in.model_dump(exclude_unset=True).items():
                setattr(data, field, value)

            await session.commit()
            await session.refresh(data)

            return TestSchema.model_validate(data)
        except StatementError:
            raise HTTPException(status_code=400, detail="Incorrect arguments")

    raise HTTPException(status_code=404, detail="User does not exist")
