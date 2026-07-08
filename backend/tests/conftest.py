"""Fixtures compartidas de prueba (sin red): FakeEmbeddings + Qdrant :memory:.

Reglas (guidelines §13): ningún test toca Ollama ni Qdrant Cloud. El vector store
usa el modo :memory: de qdrant-client y los embeddings un fake determinista.
"""

import hashlib

import pytest
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.services.rag import vectorstore as vsmod

DIM = 64


class FakeEmbeddings(Embeddings):
    """Bolsa de palabras con hashing: textos que comparten palabras se parecen;
    textos ajenos quedan casi ortogonales. Determinista, sin red."""

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * DIM
        for tok in text.lower().split():
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % DIM] += 1.0
        n = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture()
def settings_env(monkeypatch, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    data = tmp_path / "data"
    monkeypatch.setenv("DOCS_DIR", str(docs))
    monkeypatch.setenv("DATA_DIR", str(data))
    monkeypatch.setenv("QDRANT_URL", "memory")  # nadie debe usarla en tests
    monkeypatch.setenv("SCORE_THRESHOLD", "0.35")  # calibrado para FakeEmbeddings
    monkeypatch.setenv("RETRIEVER_K", "5")
    monkeypatch.setenv("RERANK_ENABLED", "false")  # sin red: el reranker descarga modelo
    get_settings.cache_clear()  # Settings está cacheado con lru_cache
    yield docs
    get_settings.cache_clear()


@pytest.fixture()
def mem_vectorstore(settings_env):
    client = QdrantClient(":memory:")
    vsmod.ensure_collection(client, DIM)
    return vsmod.get_vectorstore(client, FakeEmbeddings()), client


@pytest.fixture()
def docs_demo(settings_env):
    """Mini-corpus temporal: 2 áreas vigentes + 1 obsoleto."""
    (settings_env / "RRHH" / "Politicas").mkdir(parents=True)
    (settings_env / "Calidad" / "Procedimientos").mkdir(parents=True)
    (settings_env / "RRHH" / "Politicas" / "OBSOLETOS").mkdir()
    (settings_env / "RRHH" / "Politicas" / "vacaciones_v2.txt").write_text(
        "Politica de vacaciones: el personal dispone de 15 dias habiles anuales.",
        encoding="utf-8",
    )
    (settings_env / "Calidad" / "Procedimientos" / "auditorias_v1.txt").write_text(
        "Procedimiento de auditorias internas: se planifican cada semestre.",
        encoding="utf-8",
    )
    (settings_env / "RRHH" / "Politicas" / "OBSOLETOS" / "vacaciones_v1.txt").write_text(
        "Version antigua: 10 dias habiles.", encoding="utf-8"
    )
    return settings_env
