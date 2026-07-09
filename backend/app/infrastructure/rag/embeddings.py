from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings


def get_embeddings() -> OllamaEmbeddings:
    s = get_settings()
    return OllamaEmbeddings(model=s.ollama_embed_model, base_url=s.ollama_base_url)


def get_sparse_embeddings():
    # BM25 disperso, solo para modo híbrido; descarga un modelo pequeño
    from langchain_qdrant import FastEmbedSparse

    return FastEmbedSparse(model_name=get_settings().sparse_model)
