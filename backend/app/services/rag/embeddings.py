"""Factoría de embeddings (Ollama). Único punto para cambiar de proveedor (guidelines §4)."""

from langchain_ollama import OllamaEmbeddings

from app.core.config import get_settings


def get_embeddings() -> OllamaEmbeddings:
    s = get_settings()
    return OllamaEmbeddings(model=s.ollama_embed_model, base_url=s.ollama_base_url)
