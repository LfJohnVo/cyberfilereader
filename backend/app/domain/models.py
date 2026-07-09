"""Modelos de dominio (value objects). Tipados, sin lógica de infraestructura.

Se usa pydantic por pragmatismo (validación + serialización directa en la capa de presentación):
estos VO son a la vez el contrato interno y el DTO de la API. La regla de dependencias se mantiene
—presentación/aplicación dependen del dominio, no al revés—.
"""

from dataclasses import dataclass
from enum import StrEnum

from langchain_core.documents import Document
from pydantic import BaseModel


@dataclass
class SearchResult:
    """Resultado tipado de una recuperación: fragmentos + decisión de NO_INFO.

    `Document` (langchain-core) se usa como contenedor de datos neutral (page_content + metadata):
    acoplamiento pragmático aceptado en el ADR-0001 para no re-envolver cada fragmento.
    """

    hits: list[tuple[Document, float]]  # (fragmento, relevancia 0-1), ordenados
    found: bool  # False => nada suficientemente relevante -> NO_INFO


class Veredicto(StrEnum):
    """Resultado de un chequeo de cumplimiento."""

    CUMPLE = "cumple"
    PARCIAL = "parcial"
    NO_CUMPLE = "no_cumple"
    INDETERMINADO = "indeterminado"


class Fuente(BaseModel):
    """Fragmento citado que respalda una respuesta (con su procedencia y relevancia)."""

    n: int
    file_name: str
    source: str
    area: str
    doc_type: str | None = None
    version: str | None = None
    page: int | None = None
    score: float
    snippet: str
