import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from core.models import TestSession, Pair, Analyze
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
    session: AsyncSession, pair_id: int, block: int, telegram_id: int
):
    pair_stmt = select(Pair).where(Pair.id == pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    if telegram_id not in [pair.user_owner_telegram_id, pair.user_pair_telegram_id]:
        raise HTTPException(status_code=403, detail="User is not a member of this pair")

    stmt = (
        select(TestSession)
        .where(
            and_(
                TestSession.pair_id == pair_id,
                TestSession.telegram_id == telegram_id,
            )
        )
        .order_by(TestSession.block)
    )

    result = await session.execute(stmt)
    test_sessions = result.scalars().all()

    if not test_sessions:
        raise HTTPException(
            status_code=404, detail="No test sessions found for this pair and user"
        )

    if block:
        filtered_sessions = [ts for ts in test_sessions if ts.block == block]
        if not filtered_sessions:
            raise HTTPException(
                status_code=404, detail=f"No answers found for block {block}"
            )
        test_sessions = filtered_sessions

    user_answers = []
    for ts in test_sessions:
        questions_list = []
        if ts.questions:
            try:
                questions_list = json.loads(ts.questions)
            except json.JSONDecodeError:
                try:
                    questions_list = ast.literal_eval(ts.questions)
                except (ValueError, SyntaxError):
                    questions_list = [ts.questions]

        user_answers.append(
            {
                "session_id": ts.id,
                "block": ts.block,
                "questions": questions_list,
                "answers": ts.answer,
                "insight": ts.insight,
                "success": ts.success,
                "current_block": ts.current_block,
                "total_blocks": ts.total_blocks,
            }
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
        # Если ai_response уже не строка (например, уже словарь)
        analysis_data = ai_response if ai_response else {}

    analyze_entry = Analyze(
        pair_id=pair_id,
        telegram_id=telegram_id,
        block=block if block else 0,
        analysis_json=analysis_data,
        contradictions=[],
    )
    session.add(analyze_entry)
    await session.commit()

    # Теперь analysis_data точно определена
    return {
        "pair_id": pair_id,
        "telegram_id": telegram_id,
        "block": block if block else "all",
        "analysis": analysis_data,
        "sessions_analyzed": len(user_answers),
    }


async def generate_profile(session: AsyncSession, pair_id: int):
    # Получаем информацию о паре
    pair_stmt = select(Pair).where(Pair.id == pair_id)
    pair_result = await session.execute(pair_stmt)
    pair = pair_result.scalars().first()

    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")

    # Получаем все анализы для этой пары
    analyze_stmt = select(Analyze).where(Analyze.pair_id == pair_id)
    analyze_result = await session.execute(analyze_stmt)
    all_analyzes = analyze_result.scalars().all()

    if not all_analyzes:
        raise HTTPException(
            status_code=404, detail="No analyze data found for this pair"
        )

    # Разделяем анализы по пользователям
    user1_id = pair.user_owner_telegram_id
    user2_id = pair.user_pair_telegram_id

    user1_analyzes = [a for a in all_analyzes if a.telegram_id == user1_id]
    user2_analyzes = (
        [a for a in all_analyzes if a.telegram_id == user2_id] if user2_id else []
    )

    # Функция для создания профиля пользователя
    async def create_user_profile(analyzes, user_id, user_name="Пользователь"):
        if not analyzes:
            return None

        # Сортируем по блокам
        sorted_analyzes = sorted(analyzes, key=lambda x: x.block)

        # Формируем данные для промпта
        analyses_data = []
        for a in sorted_analyzes:
            analyses_data.append(
                {
                    "block": a.block,
                    "analysis": a.analysis_json,
                    "contradictions": a.contradictions,
                }
            )

        # Отправляем запрос к ИИ
        ai_response = await ai.deepseek(
            prompt=profile_prompt.format(
                user_id,
                user_name,
                json.dumps(analyses_data, ensure_ascii=False, indent=2, default=str),
            ),
            system_prompt=profile_system_prompt,
        )

        # Обрабатываем ответ
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

    # Создаем профили для обоих пользователей
    user1_profile = await create_user_profile(
        user1_analyzes, user1_id, "Пользователь 1"
    )
    user2_profile = (
        await create_user_profile(user2_analyzes, user2_id, "Пользователь 2")
        if user2_analyzes
        else None
    )

    # Анализ совместимости профилей (если есть оба пользователя)
    compatibility_analysis = None
    if (
        user1_profile
        and user2_profile
        and "error" not in user1_profile
        and "error" not in user2_profile
    ):

        ai_response = await ai.claude(
            prompt=compatibility_prompt.format(
                json.dumps(user1_profile, ensure_ascii=False, indent=2, default=str),
                json.dumps(user2_profile, ensure_ascii=False, indent=2, default=str),
            ),
            system_prompt=compatibility_system_prompt,
        )

        if isinstance(ai_response, str):
            cleaned = ai_response.replace("```json", "").replace("```", "").strip()
            try:
                compatibility_analysis = json.loads(cleaned)
            except:
                json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if json_match:
                    try:
                        compatibility_analysis = json.loads(json_match.group())
                    except:
                        compatibility_analysis = {
                            "error": "Failed to parse compatibility"
                        }
                else:
                    compatibility_analysis = {"error": "No JSON found"}

    # Подсчитываем противоречия
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

    return {
        "pair_id": pair_id,
        "user1_id": user1_id,
        "user2_id": user2_id,
        "profiles": {"user1": user1_profile, "user2": user2_profile},
        "compatibility": compatibility_analysis,
        "statistics": {
            "user1_analyzes_count": len(user1_analyzes),
            "user2_analyzes_count": len(user2_analyzes),
            "user1_contradictions_count": user1_contradictions,
            "user2_contradictions_count": user2_contradictions,
            "has_contradictions": user1_contradictions > 0 or user2_contradictions > 0,
        },
    }


async def generate_passport(session: AsyncSession, pair_id: int):
    # Сначала получаем профили через generate_profile
    profile_result = await generate_profile(session, pair_id)

    if not profile_result:
        raise HTTPException(
            status_code=404, detail="Could not generate profiles for this pair"
        )

    profiles = profile_result.get("profiles", {})
    user1_profile = profiles.get("user1")
    user2_profile = profiles.get("user2")

    if not user1_profile or not user2_profile:
        raise HTTPException(
            status_code=404,
            detail="Both user profiles required for passport generation",
        )

    # Формируем промпт для создания паспорта

    # Отправляем запрос к ИИ
    ai_response = await ai.claude(
        prompt=passport_prompt.format(
            json.dumps(user1_profile, ensure_ascii=False, indent=2, default=str),
            json.dumps(user2_profile, ensure_ascii=False, indent=2, default=str),
        ),
        system_prompt=passport_system_prompt,
    )

    # Обрабатываем ответ
    if isinstance(ai_response, str):
        cleaned = ai_response.replace("```json", "").replace("```", "").strip()
        try:
            passport_data = json.loads(cleaned)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                try:
                    passport_data = json.loads(json_match.group())
                except:
                    passport_data = {
                        "error": "Failed to parse JSON",
                        "raw_response": cleaned[:500],
                    }
            else:
                passport_data = {
                    "error": "No JSON found",
                    "raw_response": cleaned[:500],
                }
    else:
        passport_data = ai_response or {}

    # Можно сохранить паспорт в БД, если нужно
    # from core.models import Passport
    # passport_entry = Passport(
    #     pair_id=pair_id,
    #     passport_data=passport_data
    # )
    # session.add(passport_entry)
    # await session.commit()

    return {
        "pair_id": pair_id,
        "user1_id": profile_result["user1_id"],
        "user2_id": profile_result["user2_id"],
        "passport": passport_data,
        "generated_at": datetime.utcnow().isoformat(),
    }
