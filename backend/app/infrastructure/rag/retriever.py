import logging

from langchain_core.documents import Document
from qdrant_client import models

from app.core.config import get_settings
from app.domain.models import SearchResult

log = logging.getLogger(__name__)


def build_filter(areas: list[str] | None) -> models.Filter:
    must = [models.FieldCondition(key="metadata.estado", match=models.MatchValue(value="vigente"))]
    if areas and "*" not in areas:  # "*" = acceso total (Dirección/Auditoría)
        must.append(models.FieldCondition(key="metadata.area", match=models.MatchAny(any=areas)))
    return models.Filter(must=must)


def _normalize_rrf(raw: list[tuple[Document, float]]) -> list[tuple[Document, float]]:
    # Los scores RRF no son coseno; se normalizan a [0,1] por el máximo.
    if not raw:
        return []
    mx = max((sc for _, sc in raw), default=1.0) or 1.0
    return [(d, round(sc / mx, 3)) for d, sc in raw]


def search(vectorstore, query: str, areas: list[str] | None) -> SearchResult:
    s = get_settings()
    filtro = build_filter(areas)
    k = s.rerank_candidates if s.rerank_enabled else s.retriever_k
    raw = vectorstore.similarity_search_with_score(query, k=k, filter=filtro)

    if s.hybrid_enabled:
        hits = _normalize_rrf(raw)[: s.retriever_k]
        return SearchResult(hits=hits, found=bool(hits))

    gated = [(d, sc) for d, sc in raw if sc >= s.score_threshold]
    if not gated:
        return SearchResult(hits=[], found=False)
    if not s.rerank_enabled:
        return SearchResult(hits=gated[: s.retriever_k], found=True)
    try:
        from app.infrastructure.rag.reranker import rerank

        return SearchResult(hits=rerank(query, gated)[: s.retriever_k], found=True)
    except Exception:
        log.warning("Reranker no disponible; se usa el orden denso", exc_info=True)
        return SearchResult(hits=gated[: s.retriever_k], found=True)


def retrieve(vectorstore, query: str, areas: list[str] | None) -> list[tuple[Document, float]]:
    return search(vectorstore, query, areas).hits
