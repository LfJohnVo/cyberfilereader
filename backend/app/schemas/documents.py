"""Schemas Pydantic de documentos indexados (guidelines §5)."""

from pydantic import BaseModel


class DocumentItem(BaseModel):
    source: str
    area: str | None = None
    estado: str | None = None
    chunks: int | None = None
    sha256: str | None = None


class DocumentsResponse(BaseModel):
    total: int
    items: list[DocumentItem]


class AreasResponse(BaseModel):
    areas: list[str]
