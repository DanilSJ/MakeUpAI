from fastapi import HTTPException
from sqlalchemy.exc import StatementError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from core.models import TestSession, Pair, SubTestSession
from .schemas import RegisterSchema, SubmitSchema, SubTestSchema
from ..ai.utils import ai


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


async def submit_test(session: AsyncSession, data_in: SubmitSchema) -> SubTestSchema:
    """
    Создает новый SubTestSession с AI-сгенерированным insight'ом
    и привязывает его к существующей TestSession
    """
    # Находим тестовую сессию
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
        # Формируем промпт для DeepSeek на основе вопроса из тестовой сессии и ответа пользователя
        prompt = f"""
Вопрос: {data_in.questions}

Ответ пользователя: {data_in.answer}

На основе предоставленного вопроса и ответа, дай психологический анализ ответа пользователя.
Опиши:
1. Эмоциональное состояние
2. Ключевые психологические аспекты
3. Рекомендации
4. Инсайты о личности

Анализ должен быть кратким, но содержательным (3-5 предложений).
"""

        system_prompt = """Ты — профессиональный психологический аналитик с многолетним опытом. 
Твоя задача — анализировать ответы людей на психологические вопросы, выявлять глубинные мотивы, 
эмоциональные состояния и паттерны поведения. Ты даешь объективный, профессиональный анализ, 
основанный на принципах психологии. Избегай поверхностных суждений, будь эмпатичным, 
но профессиональным. Твои инсайты должны помогать людям лучше понять себя."""
        # Генерируем insight с помощью DeepSeek
        generated_insight = await ai.deepseek(
            prompt=prompt, system_prompt=system_prompt
        )

        # Создаем новый под-тест с сгенерированным insight'ом
        subtest = SubTestSession(
            test_session_id=test_session.id,  # 👈 вот это главное
            questions=data_in.questions,
            answer=data_in.answer,
            insight=generated_insight,
            success=data_in.success,
            current_block=data_in.current_block,
            total_blocks=data_in.total_blocks,
        )

        session.add(subtest)

        # Обновляем основную тестовую сессию (опционально)
        # Можно обновлять текущий блок или другие поля, если нужно
        if data_in.current_block is not None:
            test_session.current_block = data_in.current_block
        if data_in.total_blocks is not None:
            test_session.total_blocks = data_in.total_blocks

        await session.commit()
        await session.refresh(subtest)

        # Возвращаем созданный под-тест в виде схемы
        return SubTestSchema.model_validate(subtest)

    except StatementError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Incorrect arguments")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# Дополнительная функция для получения всех под-тестов тестовой сессии
# Дополнительная функция для получения всех под-тестов тестовой сессии
async def get_test_subtests(
    session: AsyncSession, pair_id: int, telegram_id: int
) -> list[SubTestSchema]:
    """
    Получает все под-тесты для тестовой сессии пользователя
    """
    from sqlalchemy.orm import selectinload

    # Единый запрос с жадной загрузкой (eager loading)
    stmt = (
        select(TestSession)
        .where(
            and_(
                TestSession.pair_id == pair_id,
                TestSession.telegram_id == telegram_id,
            )
        )
        .options(selectinload(TestSession.subtestsessions))
    )

    result = await session.execute(stmt)
    test_session = result.scalars().first()

    if not test_session:
        raise HTTPException(
            status_code=404,
            detail="Тестовая сессия не найдена",
        )

    # Теперь subtestsessions уже загружены, преобразуем в схемы
    return [
        SubTestSchema.model_validate(subtest)
        for subtest in test_session.subtestsessions
    ]
