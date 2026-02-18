# schemas.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AnalyzeResponseSchema(BaseModel):
    pair_id: int
    telegram_id: int
    analysis: Dict[str, Any]
    sessions_analyzed: Optional[int] = None
    subtests_analyzed: Optional[int] = None
    note: Optional[str] = None
    analyze_complete: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class AnalyzeSchema(BaseModel):
    id: int
    pair_id: int
    telegram_id: int
    block: int
    analysis_json: Optional[Dict[str, Any]] = None
    contradictions: Optional[List[Any]] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    test_id: int

    model_config = ConfigDict(from_attributes=True)


class ProfileResponseSchema(BaseModel):
    pair_id: int
    user1_id: int
    user2_id: Optional[int] = None
    profiles: Dict[str, Any]
    compatibility: Optional[Dict[str, Any]] = None
    statistics: Optional[Dict[str, Any]] = None  # Сделали опциональным
    note: Optional[str] = None
    profile_complete: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class PassportResponseSchema(BaseModel):
    pair_id: int
    user1_id: int
    user2_id: int
    passport: Dict[str, Any]
    generated_at: str
    note: Optional[str] = None
    passport_complete: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
