from pydantic import BaseModel, ConfigDict


class PairSchema(BaseModel):
    id: int
    user_owner_telegram_id: int
    user_pair_telegram_id: int | None
    invite_code: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    telegram_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)

class InviteSchema(BaseModel):
    user_pair_telegram_id: int
    invite_code: str

    model_config = ConfigDict(from_attributes=True)

