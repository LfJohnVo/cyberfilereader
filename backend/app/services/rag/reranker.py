"""Reordenamiento de candidatos con un cross-encoder (fastembed).

El recuperador denso trae varios candidatos por similitud coseno; el cross-encoder
puntúa cada par consulta-fragmento y suele ordenar mejor la relevancia real. El modelo
se carga una sola vez.
"""

import logging
import math
from functools import lru_cache

from langchain_core.documents import Document

from app.core.config import get_settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _encoder():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    name = get_settings().rerank_model
    log.info("Cargando reranker %s", name)
    return TextCrossEncoder(model_name=name)


def rerank(query: str, hits: list[tuple[Document, float]]) -> list[tuple[Document, float]]:
    """Ordena (doc, score) de mayor a menor por relevancia del cross-encoder (0-1)."""
    docs = [d for d, _ in hits]
    raw = _encoder().rerank(query, [d.page_content for d in docs])
    ranked = sorted(zip(docs, raw, strict=True), key=lambda ds: ds[1], reverse=True)
    return [(d, 1.0 / (1.0 + math.exp(-float(s)))) for d, s in ranked]
