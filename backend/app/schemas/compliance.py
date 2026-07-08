"""Schema de respuesta del chequeo de cumplimiento (guidelines §5)."""

from pydantic import BaseModel

from app.schemas.chat import Source


class ComplianceResponse(BaseModel):
    file_name: str
    verdict: str  # "cumple" | "parcial" | "no_cumple" | "indeterminado"
    report: str
    sources: list[Source]
