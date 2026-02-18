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
        # Если анализ уже существует, возвращаем его
        return {
            "pair_id": pair_id,
            "telegram_id": telegram_id,
            "analysis": existing_analyze.analysis_json,
            "note": "Analysis already exists for this user",
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
            json.dumps(user_answers, ensure_ascii=False, indent=2, default=str),
        ),
        system_prompt=system_prompt,
    )

    if isinstance(ai_response, str):
        cleaned = ai_response.replace("```json", "").replace("```", "").strip()
        try:
            analysis_data = json.loads(cleaned)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                try:
                    analysis_data = json.loads(json_match.group())
                except:
                    analysis_data = {
                        "error": "Failed to parse JSON",
                        "raw_response": cleaned,
                    }
            else:
                analysis_data = {"error": "No JSON found", "raw_response": cleaned}
    else:
        analysis_data = ai_response if ai_response else {}

    analyze_entry = Analyze(
        pair_id=pair_id,
        telegram_id=telegram_id,
        block=0,
        analysis_json=analysis_data,
        contradictions=[],
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

    return {
        "pair_id": pair_id,
        "telegram_id": telegram_id,
        "analysis": analysis_data,
        "sessions_analyzed": len(test_sessions),
        "subtests_analyzed": len(user_answers),
        "analyze_complete": (
            pair.analyze_complete if hasattr(pair, "analyze_complete") else False
        ),
    }


async def generate_profile(session: AsyncSession, pair_id: int):
    # Получаем пару
    pair_stmt = select(Pair).where(Pair.id == pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    # Проверяем, что analyze_complete = True
    if not pair.analyze_complete:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate profile: analyzes are not complete for both users",
        )

    # Проверяем, существует ли уже профиль
    profile_stmt = select(Profile).where(Profile.pair_id == pair_id)
    profile_result = await session.execute(profile_stmt)
    existing_profile = profile_result.scalars().first()

    if existing_profile and existing_profile.profile_json:
        # Если профиль уже существует, возвращаем его
        return {
            "pair_id": pair_id,
            "user1_id": pair.user_owner_telegram_id,
            "user2_id": pair.user_pair_telegram_id,
            "profiles": existing_profile.profile_json,
            "note": "Existing profile returned",
        }

    # Получаем все анализы пары
    analyze_stmt = select(Analyze).where(Analyze.pair_id == pair_id)
    analyze_result = await session.execute(analyze_stmt)
    all_analyzes = analyze_result.scalars().all()

    if not all_analyzes:
        raise HTTPException(
            status_code=404, detail="No analyze data found for this pair"
        )

    user1_id = pair.user_owner_telegram_id
    user2_id = pair.user_pair_telegram_id

    user1_analyzes = [a for a in all_analyzes if a.telegram_id == user1_id]
    user2_analyzes = (
        [a for a in all_analyzes if a.telegram_id == user2_id] if user2_id else []
    )

    # Вспомогательная функция парсинга AI JSON
    def parse_ai_json(ai_response):
        if isinstance(ai_response, str):
            cleaned = ai_response.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        return {
                            "error": "Failed to parse JSON",
                            "raw_response": cleaned[:500],
                        }
                return {"error": "No JSON found", "raw_response": cleaned[:500]}
        return ai_response or {}

    # Создание профиля пользователя
    async def create_user_profile(analyzes, user_id, user_name):
        if not analyzes:
            return None
        sorted_analyzes = sorted(analyzes, key=lambda x: x.block)
        analyses_data = [
            {
                "block": a.block,
                "analysis": a.analysis_json,
                "contradictions": a.contradictions,
                "created_at": a.create_at.isoformat() if a.create_at else None,
            }
            for a in sorted_analyzes
        ]
        ai_response = await ai.deepseek(
            prompt=profile_prompt.format(
                user_id,
                user_name,
                json.dumps(analyses_data, ensure_ascii=False, indent=2, default=str),
            ),
            system_prompt=profile_system_prompt,
        )
        return parse_ai_json(ai_response)

    user1_profile = await create_user_profile(
        user1_analyzes, user1_id, "Пользователь 1"
    )
    user2_profile = (
        await create_user_profile(user2_analyzes, user2_id, "Пользователь 2")
        if user2_analyzes
        else None
    )

    # Сохраняем профиль
    profile_data = {"user1": user1_profile, "user2": user2_profile}

    if existing_profile:
        existing_profile.profile_json = profile_data
    else:
        profile_obj = Profile(
            pair_id=pair_id,
            user_telegram_id=user1_id,
            profile_json=profile_data,
        )
        session.add(profile_obj)

    # Устанавливаем profile_complete = True
    pair.profile_complete = True

    # Совместимость
    compatibility_analysis = None
    if (
        user1_profile
        and user2_profile
        and "error" not in user1_profile
        and "error" not in user2_profile
    ):
        ai_response = await ai.claude(
            prompt=compatibility_prompt.format(
                json.dumps(user1_profile, ensure_ascii=False, indent=2),
                json.dumps(user2_profile, ensure_ascii=False, indent=2),
            ),
            system_prompt=compatibility_system_prompt,
        )
        compatibility_analysis = parse_ai_json(ai_response)

    # Статистика
    user1_contradictions = (
        len(user1_profile.get("inconsistencies", []))
        if user1_profile and "inconsistencies" in user1_profile
        else 0
    )
    user2_contradictions = (
        len(user2_profile.get("inconsistencies", []))
        if user2_profile and "inconsistencies" in user2_profile
        else 0
    )

    await session.commit()

    return {
        "pair_id": pair_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "profiles": profile_data,
        "compatibility": compatibility_analysis,
        "statistics": {
            "user1_analyzes_count": len(user1_analyzes),
            "user2_analyzes_count": len(user2_analyzes),
            "user1_contradictions_count": user1_contradictions,
            "user2_contradictions_count": user2_contradictions,
            "has_contradictions": user1_contradictions > 0 or user2_contradictions > 0,
        },
        "profile_complete": pair.profile_complete,
    }


async def generate_passport(session: AsyncSession, pair_id: int):
    # Получаем пару
    pair_stmt = select(Pair).where(Pair.id == pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    # Проверяем, что profile_complete = True
    if not pair.profile_complete:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate passport: profile is not complete. Please generate profile first.",
        )

    # Проверяем, существует ли уже паспорт
    passport_stmt = select(Passport).where(Passport.pair_id == pair_id)
    passport_result = await session.execute(passport_stmt)
    existing_passport = passport_result.scalars().first()

    # Если паспорт уже существует, просто возвращаем его
    if existing_passport and existing_passport.passport_json:
        return {
            "pair_id": pair_id,
            "user1_id": pair.user_owner_telegram_id,
            "user2_id": pair.user_pair_telegram_id,
            "passport": existing_passport.passport_json,
            "generated_at": (
                existing_passport.created_at.isoformat()
                if hasattr(existing_passport, "created_at")
                else datetime.utcnow().isoformat()
            ),
            "note": "Existing passport returned",
            "passport_complete": pair.passport_complete,
        }

    # Получаем профиль пары
    profile_stmt = select(Profile).where(Profile.pair_id == pair_id)
    profile_result = await session.execute(profile_stmt)
    profile = profile_result.scalars().first()

    if not profile or not profile.profile_json:
        raise HTTPException(
            status_code=404,
            detail="Profile not found or empty for this pair. Please generate profile first.",
        )

    profile_data = profile.profile_json

    # Отправляем весь JSON в ИИ
    ai_response = await ai.deepseek(
        prompt=passport_prompt.format(
            json.dumps(profile_data, ensure_ascii=False, indent=2, default=str)
        ),
        system_prompt=passport_system_prompt,
    )

    # Парсим ответ AI, чтобы получить словарь
    if isinstance(ai_response, str):
        # Пытаемся извлечь JSON из ответа
        cleaned = ai_response.replace("```json", "").replace("```", "").strip()
        try:
            passport_data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Если не удалось распарсить как JSON, ищем JSON в тексте
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                try:
                    passport_data = json.loads(json_match.group())
                except:
                    # Если все еще не удалось, создаем структуру с текстовым ответом
                    passport_data = {
                        "content": cleaned,
                        "format": "text",
                        "note": "Response is in text format",
                    }
            else:
                # Создаем словарь с текстовым ответом
                passport_data = {
                    "content": cleaned,
                    "format": "text",
                    "note": "Response is in text format",
                }
    else:
        passport_data = ai_response if ai_response else {}

    # Сохраняем паспорт
    if existing_passport:
        existing_passport.passport_json = passport_data
    else:
        new_passport = Passport(pair_id=pair_id, passport_json=passport_data)
        session.add(new_passport)

    # Устанавливаем passport_complete = True
    pair.passport_complete = True

    # Сохраняем изменения
    await session.commit()

    return {
        "pair_id": pair_id,
        "user1_id": pair.user_owner_telegram_id,
        "user2_id": pair.user_pair_telegram_id,
        "passport": passport_data,
        "generated_at": datetime.utcnow().isoformat(),
        "passport_complete": pair.passport_complete,
    }
