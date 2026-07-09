"""Schemas Pydantic del chat (guidelines §5: contratos explícitos).

El DTO de fuente ES el value object de dominio `Fuente` (presentación depende de dominio).
"""

from pydantic import BaseModel, Field

from app.domain.models import Fuente

Source = Fuente  # alias de compatibilidad


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=64)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Fuente]
    no_info: bool
    status: str  # estado final del agente: "idle" | "no_info" | "error"
    session_id: str
