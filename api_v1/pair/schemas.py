from pydantic import BaseModel, ConfigDict
from typing import Optional


class PairSchema(BaseModel):
    id: int
    user_owner_telegram_id: int
    user_pair_telegram_id: int | None = None
    invite_code: str

    user_owner_complete_test: bool
    user_pair_complete_test: bool
    analyze_complete: bool
    profile_complete: bool
    passport_complete: bool

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    user_owner_telegram_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class InviteSchema(BaseModel):
    user_pair_telegram_id: int
    invite_code: str

    model_config = ConfigDict(from_attributes=True)


class UpdateStatusSchema(BaseModel):
    status: Optional[str] = None
    user_owner_complete_test: Optional[bool] = None
    user_pair_complete_test: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
