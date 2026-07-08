"""Búsqueda semántica con filtro de estado + áreas permitidas y umbral de score."""

from langchain_core.documents import Document
from qdrant_client import models

from app.core.config import get_settings


def build_filter(areas: list[str] | None) -> models.Filter:
    must = [models.FieldCondition(key="metadata.estado", match=models.MatchValue(value="vigente"))]
    if areas and "*" not in areas:  # "*" = perfil con acceso total (Dirección/Auditoría)
        must.append(models.FieldCondition(key="metadata.area", match=models.MatchAny(any=areas)))
    return models.Filter(must=must)


def retrieve(vectorstore, query: str, areas: list[str] | None) -> list[tuple[Document, float]]:
    s = get_settings()
    hits = vectorstore.similarity_search_with_score(
        query, k=s.retriever_k, filter=build_filter(areas)
    )
    # Con distancia COSINE, Qdrant devuelve similitud (mayor = mejor).
    return [(d, score) for d, score in hits if score >= s.score_threshold]
