from pydantic import BaseModel, ConfigDict


class UserSchema(BaseModel):
    id: int
    telegram_id: int
    username: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    telegram_id: int
    username: str
    status: str

    model_config = ConfigDict(from_attributes=True)
