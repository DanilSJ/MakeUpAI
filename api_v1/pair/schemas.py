from pydantic import BaseModel, ConfigDict


class PairSchema(BaseModel):
    id: int
    user_owner_telegram_id: int
    user_pair_telegram_id: int | None = None
    invite_code: str
    status: str

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
    status: str

    model_config = ConfigDict(from_attributes=True)
