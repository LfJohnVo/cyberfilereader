from dataclasses import dataclass
from enum import StrEnum

from langchain_core.documents import Document
from pydantic import BaseModel


@dataclass
class SearchResult:
    hits: list[tuple[Document, float]]
    found: bool  # False => nada relevante -> NO_INFO


class Veredicto(StrEnum):
    CUMPLE = "cumple"
    PARCIAL = "parcial"
    NO_CUMPLE = "no_cumple"
    INDETERMINADO = "indeterminado"


class Fuente(BaseModel):
    n: int
    file_name: str
    source: str
    area: str
    doc_type: str | None = None
    version: str | None = None
    page: int | None = None
    score: float
    snippet: str
