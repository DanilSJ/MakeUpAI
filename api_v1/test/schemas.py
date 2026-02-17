from pydantic import BaseModel, ConfigDict, Field


class TestSessionBase(BaseModel):
    telegram_id: int
    pair_id: int
    block: int


class TestSessionCreate(TestSessionBase):
    pass


class TestSessionUpdate(BaseModel):
    answers: str | None = None
    insight: str | None = None
    success: bool | None = None
    current_block: int | None = None
    total_blocks: int | None = None
    questions: str | None = None


class TestSchema(TestSessionBase):
    id: int
    questions: str | None = None
    answers: str | None = None
    insight: str | None = None
    success: bool | None = False
    current_block: int | None = None
    total_blocks: int | None = None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(TestSessionBase):
    model_config = ConfigDict(from_attributes=True)


class SubmitSchema(BaseModel):
    telegram_id: int
    pair_id: int
    answers: str
    insight: str | None = None
    success: bool | None = None
    current_block: int | None = None
    total_blocks: int | None = None

    model_config = ConfigDict(from_attributes=True)


# Схема для ответа с дополнительной информацией о паре
class TestSessionWithPairSchema(TestSchema):
    pair_owner_id: int
    pair_partner_id: int | None

    model_config = ConfigDict(from_attributes=True)
