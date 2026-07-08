"""Schemas Pydantic del chat (guidelines §5: contratos explícitos)."""

from pydantic import BaseModel, Field


class Source(BaseModel):
    n: int
    file_name: str
    source: str
    area: str
    doc_type: str | None = None
    version: str | None = None
    page: int | None = None
    score: float
    snippet: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=64)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    no_info: bool
    status: str  # estado final del agente: "idle" | "no_info" | "error"
    session_id: str
