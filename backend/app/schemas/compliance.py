from pydantic import BaseModel

from app.domain.models import Fuente, Veredicto


class ComplianceResponse(BaseModel):
    file_name: str
    verdict: Veredicto
    report: str
    sources: list[Fuente]
