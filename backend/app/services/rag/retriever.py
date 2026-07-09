"""Recuperación: filtro de estado + áreas, umbral, reranking, y un resultado TIPADO.

`search()` es la autoridad única de recuperación: decide NO_INFO de forma coherente
(independiente de qué flags estén activos) y normaliza el `score` a un rango [0,1] comparable,
para que los consumidores (chat, compliance, MCP, agente) no tengan que interpretar tres escalas
distintas (coseno / RRF / cross-encoder). `retrieve()` es un envoltorio de compatibilidad.
"""

import logging
from dataclasses import dataclass

from langchain_core.documents import Document
from qdrant_client import models

from app.core.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class SearchResult:
    hits: list[tuple[Document, float]]  # (doc, relevancia 0-1), ordenados de mayor a menor
    found: bool  # False => nada suficientemente relevante -> NO_INFO


def build_filter(areas: list[str] | None) -> models.Filter:
    must = [models.FieldCondition(key="metadata.estado", match=models.MatchValue(value="vigente"))]
    if areas and "*" not in areas:  # "*" = perfil con acceso total (Dirección/Auditoría)
        must.append(models.FieldCondition(key="metadata.area", match=models.MatchAny(any=areas)))
    return models.Filter(must=must)


def _normalize_rrf(raw: list[tuple[Document, float]]) -> list[tuple[Document, float]]:
    """Los scores RRF (híbrido) no son coseno; se normalizan a [0,1] por el máximo."""
    if not raw:
        return []
    mx = max((sc for _, sc in raw), default=1.0) or 1.0
    return [(d, round(sc / mx, 3)) for d, sc in raw]


def search(vectorstore, query: str, areas: list[str] | None) -> SearchResult:
    """Recupera y decide relevancia de forma unificada. Devuelve hits con score [0,1] + found."""
    s = get_settings()
    filtro = build_filter(areas)
    k = s.rerank_candidates if s.rerank_enabled else s.retriever_k
    raw = vectorstore.similarity_search_with_score(query, k=k, filter=filtro)

    if s.hybrid_enabled:
        # Híbrido: el score es RRF (otra escala). Se normaliza a [0,1]; el gate fino de NO_INFO
        # se delega en CRAG (recomendado activarlo con híbrido). Sin resultados -> NO_INFO.
        hits = _normalize_rrf(raw)[: s.retriever_k]
        return SearchResult(hits=hits, found=bool(hits))

    # Denso: el umbral coseno es el gate de NO_INFO.
    gated = [(d, sc) for d, sc in raw if sc >= s.score_threshold]
    if not gated:
        return SearchResult(hits=[], found=False)
    if not s.rerank_enabled:
        return SearchResult(hits=gated[: s.retriever_k], found=True)
    # Rerank: reordena los que ya pasaron el gate; su score sale ya normalizado (sigmoide 0-1).
    try:
        from app.services.rag.reranker import rerank

        return SearchResult(hits=rerank(query, gated)[: s.retriever_k], found=True)
    except Exception:
        log.warning("Reranker no disponible; se usa el orden denso", exc_info=True)
        return SearchResult(hits=gated[: s.retriever_k], found=True)


def retrieve(vectorstore, query: str, areas: list[str] | None) -> list[tuple[Document, float]]:
    """Envoltorio de compatibilidad: solo los hits (sin el estado tipado de NO_INFO)."""
    return search(vectorstore, query, areas).hits
