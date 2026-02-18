from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from core.models import SubscriptionType


class UserSchema(BaseModel):
    id: int
    telegram_id: int
    username: str
    status: str
    admin: bool

    # Подписка
    subscription: SubscriptionType
    ai_question: int
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    ai_recharge_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    telegram_id: int
    username: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class UpdateUserSchema(BaseModel):
    status: str

    model_config = ConfigDict(from_attributes=True)


# ==============================
# НОВЫЕ СХЕМЫ
# ==============================


class UpdateSubscriptionSchema(BaseModel):
    subscription: SubscriptionType
    subscription_end: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateAIQuestionSchema(BaseModel):
    ai_question: int

    model_config = ConfigDict(from_attributes=True)


class UpdateAIRechargeTimeSchema(BaseModel):
    ai_recharge_time: datetime

    model_config = ConfigDict(from_attributes=True)
