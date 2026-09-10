from pydantic import BaseModel


class ChatQuery(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sql: str | None = None
    columns: list[str] = []
    rows: list[dict] = []
