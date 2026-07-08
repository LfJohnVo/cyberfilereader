"""Búsqueda semántica: filtro de estado + áreas permitidas, umbral y reordenamiento."""

import logging

from langchain_core.documents import Document
from qdrant_client import models

from app.core.config import get_settings

log = logging.getLogger(__name__)


def build_filter(areas: list[str] | None) -> models.Filter:
    must = [models.FieldCondition(key="metadata.estado", match=models.MatchValue(value="vigente"))]
    if areas and "*" not in areas:  # "*" = perfil con acceso total (Dirección/Auditoría)
        must.append(models.FieldCondition(key="metadata.area", match=models.MatchAny(any=areas)))
    return models.Filter(must=must)


def retrieve(vectorstore, query: str, areas: list[str] | None) -> list[tuple[Document, float]]:
    s = get_settings()
    filtro = build_filter(areas)
    # Con reranking traemos más candidatos densos y el cross-encoder elige el top-k final.
    k = s.rerank_candidates if s.rerank_enabled else s.retriever_k
    hits = vectorstore.similarity_search_with_score(query, k=k, filter=filtro)
    # Umbral coseno: decide si hay algo suficientemente relevante (si no -> NO_INFO).
    hits = [(d, score) for d, score in hits if score >= s.score_threshold]
    if not hits or not s.rerank_enabled:
        return hits[: s.retriever_k]
    try:
        from app.services.rag.reranker import rerank

        return rerank(query, hits)[: s.retriever_k]
    except Exception:
        log.warning("Reranker no disponible; se usa el orden denso", exc_info=True)
        return hits[: s.retriever_k]
