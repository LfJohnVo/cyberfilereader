"""Única fuente de configuración. Nadie más lee variables de entorno (guidelines §4.3)."""

from functools import lru_cache

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

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retriever_k: int = 5
    score_threshold: float = 0.50  # recalibrar por modelo de embeddings (ver tests/eval)

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_num_ctx: int = 8192
    llm_temperature: float = 0.1

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "sgi_docs"

    database_url: str = ""  # prod
    redis_url: str = ""  # prod
    jwt_secret: str = "dev-only"
    jwt_expire_minutes: int = 480

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",")}


@lru_cache
def get_settings() -> Settings:
    return Settings()
