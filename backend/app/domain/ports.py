"""Puertos de la arquitectura hexagonal (interfaces)."""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from langchain_core.documents import Document

from app.domain.models import SearchResult


@runtime_checkable
class LlmPort(Protocol):
    def invoke(self, messages: list) -> Any: ...


@runtime_checkable
class EmbeddingsPort(Protocol):
    def embed_query(self, text: str) -> list[float]: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class VectorStorePort(Protocol):
    def similarity_search_with_score(
        self, query: str, k: int, filter: Any
    ) -> list[tuple[Document, float]]: ...
    def add_documents(self, documents: list[Document]) -> Any: ...


@runtime_checkable
class RetrieverPort(Protocol):
    def search(self, query: str, areas: list[str] | None) -> SearchResult: ...


@runtime_checkable
class MemoryPort(Protocol):
    def get_history(self, session_id: str) -> list[tuple[str, str]]: ...
    def append(self, session_id: str, role: str, content: str) -> None: ...
    def clear(self, session_id: str) -> None: ...


@runtime_checkable
class DocumentLoaderPort(Protocol):
    def load_file(self, path: Path) -> list[Document]: ...
