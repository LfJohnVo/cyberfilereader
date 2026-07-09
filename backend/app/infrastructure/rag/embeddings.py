"""Factoría de embeddings. Único punto para cambiar de proveedor (guidelines §4).

Denso: Ollama (semántico). Disperso: FastEmbed BM25 (léxico), solo para el modo híbrido.
"""

from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings


def get_embeddings() -> OllamaEmbeddings:
    s = get_settings()
    return OllamaEmbeddings(model=s.ollama_embed_model, base_url=s.ollama_base_url)


def get_sparse_embeddings():
    """Embedding disperso BM25 (FastEmbed) para búsqueda híbrida. Descarga un modelo pequeño."""
    from langchain_qdrant import FastEmbedSparse

    return FastEmbedSparse(model_name=get_settings().sparse_model)
