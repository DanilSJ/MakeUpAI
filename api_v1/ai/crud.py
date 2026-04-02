import re
from datetime import datetime
from sqlalchemy.orm import selectinload

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from core.models import TestSession, Pair, Analyze, SubTestSession, Profile, Passport
from .prompt import (
    system_prompt,
    prompt_template,
    passport_prompt,
    passport_system_prompt,
    profile_system_prompt,
    profile_prompt,
    compatibility_prompt,
    compatibility_system_prompt,
)
from .utils import ai
import json
import ast


async def analyze_create(
    session: AsyncSession,
    pair_id: int,
    telegram_id: int,
):
    pair_stmt = select(Pair).where(Pair.id == pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    if telegram_id not in [pair.user_owner_telegram_id, pair.user_pair_telegram_id]:
        raise HTTPException(status_code=403, detail="User is not a member of this pair")

    # Проверяем, делал ли пользователь уже анализ
    existing_analyze_stmt = select(Analyze).where(
        and_(Analyze.pair_id == pair_id, Analyze.telegram_id == telegram_id)
    )
    existing_analyze_result = await session.execute(existing_analyze_stmt)
    existing_analyze = existing_analyze_result.scalars().first()

    if existing_analyze:
        # FIX Баг 3: Даже при раннем возврате проверяем analyze_complete
        # и возвращаем его в ответе
        return {
            "pair_id": pair_id,
            "telegram_id": telegram_id,
            "analysis": existing_analyze.analysis_json,
            "note": "Analysis already exists for this user",
            "analyze_complete": pair.analyze_complete,
        }

    # Получаем тестовые сессии с подгруженными под-тестами
    stmt = (
        select(TestSession)
        .where(
            and_(
                TestSession.pair_id == pair_id,
                TestSession.telegram_id == telegram_id,
            )
        )
        .options(selectinload(TestSession.subtestsessions))
        .order_by(TestSession.block)
    )

    result = await session.execute(stmt)
    test_sessions = result.scalars().all()

    if not test_sessions:
        raise HTTPException(
            status_code=404, detail="No test sessions found for this pair and user"
        )

    # Собираем данные из под-тестов
    user_answers = []
    for ts in test_sessions:
        for subtest in ts.subtestsessions:
            questions_list = []
            if subtest.questions:
                try:
                    questions_list = json.loads(subtest.questions)
                except json.JSONDecodeError:
                    try:
                        questions_list = ast.literal_eval(subtest.questions)
                    except (ValueError, SyntaxError):
                        questions_list = [subtest.questions]

            user_answers.append(
                {
                    "test_session_id": ts.id,
                    "subtest_id": subtest.id,
                    "block": ts.block,
                    "questions": questions_list,
                    "answers": subtest.answer,
                    "insight": subtest.insight,
                    "success": subtest.success,
                    "current_block": subtest.current_block,
                    "total_blocks": subtest.total_blocks,
                    "created_at": (
                        subtest.create_at.isoformat() if subtest.create_at else None
                    ),
                }
            )

    if not user_answers:
        raise HTTPException(
            status_code=404, detail="No subtests found for the specified test sessions"
        )

    ai_response = await ai.deepseek(
        prompt=prompt_template.format(
            telegram_id,
            pair_id,
            pair.user_owner_telegram_id,
            pair.user_pair_telegram_id or "не указан",
            str(user_answers),
        ),
        system_prompt=system_prompt,
    )

    analysis_data = ai_response

    analyze_entry = Analyze(
        pair_id=pair_id,
        telegram_id=telegram_id,
        block=0,
        analysis_json=analysis_data,
    )

    session.add(analyze_entry)

    # Проверяем, сделали ли оба пользователя анализ
    other_user_id = (
        pair.user_pair_telegram_id
        if telegram_id == pair.user_owner_telegram_id
        else pair.user_owner_telegram_id
    )

    other_user_analyze_stmt = select(Analyze).where(
        and_(Analyze.pair_id == pair_id, Analyze.telegram_id == other_user_id)
    )
    other_user_analyze_result = await session.execute(other_user_analyze_stmt)
    other_user_analyze = other_user_analyze_result.scalars().first()

    # Если оба пользователя сделали анализ, устанавливаем analyze_complete = True
    if other_user_analyze:
        pair.analyze_complete = True

    await session.commit()

    # FIX Баг 1: Автоматический запуск цепочки profile → passport
    # Когда оба пользователя завершили анализ, автоматически генерируем
    # профиль и паспорт без отдельных вызовов API
    passport_text = None
    if pair.analyze_complete and not pair.passport_complete:
        try:
            profile_result = await generate_profile(session=session, pair_id=pair_id)
            passport_result = await generate_passport(session=session, pair_id=pair_id)
            passport_text = passport_result.get("passport")
        except Exception as e:
            # Логируем ошибку, но не роняем основной ответ
            print(
                f"[AUTO-PIPELINE] Error generating profile/passport for pair {pair_id}: {e}"
            )

    return {
        "pair_id": pair_id,
        "telegram_id": telegram_id,
        "analysis": analysis_data,
        "sessions_analyzed": len(test_sessions),
        "subtests_analyzed": len(user_answers),
        "analyze_complete": pair.analyze_complete,
        # Новое поле — если паспорт сгенерирован автоматически, он тут
        "passport": passport_text,
        "passport_complete": (
            pair.passport_complete if hasattr(pair, "passport_complete") else False
        ),
    }


async def generate_profile(session: AsyncSession, pair_id: int):

    pair = await session.get(Pair, pair_id)

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    if not pair.analyze_complete:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate profile: analyzes are not complete for both users",
        )

    profile_stmt = select(Profile).where(Profile.pair_id == pair_id)
    profile_result = await session.execute(profile_stmt)
    existing_profile = profile_result.scalars().first()

    if existing_profile and existing_profile.profile_text:
        return {
            "pair_id": pair_id,
            "user1_id": pair.user_owner_telegram_id,
            "user2_id": pair.user_pair_telegram_id,
            "profiles": existing_profile.profile_text,
            "note": "Existing profile returned",
            "profile_complete": pair.profile_complete,
        }

    analyze_stmt = select(Analyze).where(Analyze.pair_id == pair_id)
    analyze_result = await session.execute(analyze_stmt)
    analyzes = analyze_result.scalars().all()

    if not analyzes:
        raise HTTPException(
            status_code=404, detail="No analyze data found for this pair"
        )

    user1_id = pair.user_owner_telegram_id
    user2_id = pair.user_pair_telegram_id

    user1_text = "\n\n".join(
        a.analysis_json for a in analyzes if a.telegram_id == user1_id
    )

    user2_text = "\n\n".join(
        a.analysis_json for a in analyzes if a.telegram_id == user2_id
    )

    user1_profile = await ai.deepseek(
        prompt=profile_prompt.format(user1_id, "Пользователь 1", user1_text),
        system_prompt=profile_system_prompt,
    )

    user2_profile = None

    if user2_text:
        user2_profile = await ai.deepseek(
            prompt=profile_prompt.format(user2_id, "Пользователь 2", user2_text),
            system_prompt=profile_system_prompt,
        )

    # FIX Баг 2: Генерируем совместимость ДО формирования profile_text,
    # чтобы включить её в сохранённые данные
    compatibility_analysis = None
    if user1_profile and user2_profile:
        compatibility_analysis = await ai.deepseek(
            prompt=compatibility_prompt.format(
                user1_profile,
                user2_profile,
            ),
            system_prompt=compatibility_system_prompt,
        )

    # FIX Баг 2: Включаем compatibility_analysis в profile_text,
    # чтобы он был доступен при генерации паспорта
    profile_text = f"""USER 1 PROFILE
{user1_profile}

USER 2 PROFILE
{user2_profile}"""

    if compatibility_analysis:
        profile_text += f"""

COMPATIBILITY ANALYSIS
{compatibility_analysis}"""

    if existing_profile:
        existing_profile.profile_text = profile_text
    else:
        session.add(
            Profile(
                pair_id=pair_id,
                user_telegram_id=user1_id,
                profile_text=profile_text,
            )
        )

    pair.profile_complete = True

    await session.commit()

    return {
        "pair_id": pair_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "profiles": profile_text,
        "compatibility": compatibility_analysis,
        "profile_complete": pair.profile_complete,
    }


async def generate_passport(session: AsyncSession, pair_id: int):

    pair = await session.get(Pair, pair_id)

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    # FIX: Если профиль ещё не создан, но анализ завершён —
    # автоматически генерируем профиль
    if not pair.profile_complete and pair.analyze_complete:
        await generate_profile(session=session, pair_id=pair_id)
        # Перечитываем pair после коммита в generate_profile
        await session.refresh(pair)

    if not pair.profile_complete:
        raise HTTPException(status_code=400, detail="Profile not complete")

    passport_stmt = select(Passport).where(Passport.pair_id == pair_id)
    passport_result = await session.execute(passport_stmt)
    existing_passport = passport_result.scalars().first()

    if existing_passport and existing_passport.passport_text:
        return {
            "pair_id": pair_id,
            "user1_id": pair.user_owner_telegram_id,
            "user2_id": pair.user_pair_telegram_id,
            "passport": existing_passport.passport_text,
            "generated_at": datetime.utcnow().isoformat(),
            "passport_complete": pair.passport_complete,
            "note": "Existing passport returned",
        }

    profile_stmt = select(Profile).where(Profile.pair_id == pair_id)
    profile_result = await session.execute(profile_stmt)
    profile = profile_result.scalars().first()

    if not profile or not profile.profile_text:
        raise HTTPException(status_code=404, detail="Profile not found")

    ai_response = await ai.deepseek(
        prompt=passport_prompt.format(profile.profile_text),
        system_prompt=passport_system_prompt,
    )

    passport_text = ai_response

    if existing_passport:
        existing_passport.passport_text = passport_text
    else:
        session.add(Passport(pair_id=pair_id, passport_text=passport_text))

    pair.passport_complete = True

    await session.commit()
    return {
        "pair_id": pair_id,
        "user1_id": pair.user_owner_telegram_id,
        "user2_id": pair.user_pair_telegram_id,
        "passport": passport_text,
        "generated_at": datetime.utcnow().isoformat(),
        "passport_complete": pair.passport_complete,
    }
