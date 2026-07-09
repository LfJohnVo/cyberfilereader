from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 5001
    allowed_origins: str = "http://localhost:5173"

    docs_dir: str = "./docs"
    data_dir: str = "./data"
    allowed_extensions: str = ".pdf,.docx,.txt,.md,.xlsx,.csv"
    max_file_mb: int = 25
    max_uncompressed_mb: int = 150  # tope descomprimido de .docx/.xlsx (anti zip-bomb)

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retriever_k: int = 5
    score_threshold: float = 0.50
    rerank_enabled: bool = False
    rerank_model: str = "jinaai/jina-reranker-v2-base-multilingual"
    rerank_candidates: int = 20
    hybrid_enabled: bool = False  # requiere re-ingesta (vectores nombrados)
    sparse_model: str = "Qdrant/bm25"
    condense_enabled: bool = True
    crag_enabled: bool = False

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_num_ctx: int = 8192
    ollama_request_timeout: float = 120.0
    llm_temperature: float = 0.1

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "sgi_docs"

    database_url: str = ""
    redis_url: str = ""
    jwt_secret: str = "dev-only"
    jwt_expire_minutes: int = 480

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",")}

    @model_validator(mode="after")
    def _coherencia_rag(self):
        if self.rerank_enabled and self.rerank_candidates < self.retriever_k:
            raise ValueError("RERANK_CANDIDATES debe ser >= RETRIEVER_K")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
