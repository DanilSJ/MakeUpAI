from pydantic import BaseModel, ConfigDict


class TestSchema(BaseModel):
    id: int
    pair_id: int
    block: int
    questions: list[str] | None = None
    insight: str | None = None
    success: bool | None = False
    current_block: int | None = None
    total_blocks: int | None = None
    answers: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    pair_id: int
    block: int

    model_config = ConfigDict(from_attributes=True)


class SubmitSchema(BaseModel):
    session_id: int
    answers: list[str]

    model_config = ConfigDict(from_attributes=True)
