from pydantic import BaseModel, ConfigDict


class TestSchema(BaseModel):
    id: int
    pair_id: int
    block: int
    questions: list[str] | None
    insight: str | None
    success: bool | False
    current_block: int | None
    total_blocks: int
    answers: list[str] | None

    model_config = ConfigDict(from_attributes=True)


class RegisterSchema(BaseModel):
    pair_id: int
    block: int

    model_config = ConfigDict(from_attributes=True)


class SubmitSchema(BaseModel):
    session_id: int
    answers: list[str]

    model_config = ConfigDict(from_attributes=True)
