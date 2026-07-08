"""Punto de entrada de la API SGI-Agent: lifespan, CORS, rate limiting y routers."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import chat, compliance, documents, health, history, ingest
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.rag.embeddings import get_embeddings
from app.services.rag.llm import get_chat_model
from app.services.rag.vectorstore import ensure_collection, get_client, get_vectorstore

s = get_settings()
setup_logging()
log = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    embeddings = get_embeddings()
    client = get_client()

    # Garantiza que la colección existe en Qdrant antes de construir el vectorstore.
    # Hace un embed de prueba para conocer la dimensión del modelo configurado.
    try:
        dim = len(embeddings.embed_query("probe"))
        ensure_collection(client, dim)
    except Exception:
        log.exception(
            "No se pudo garantizar la colección Qdrant; "
            "verifica QDRANT_URL, QDRANT_API_KEY y conectividad."
        )
        raise

    app.state.qdrant = client
    app.state.vectorstore = get_vectorstore(client, embeddings)
    app.state.llm = get_chat_model()
    log.info("SGI-Agent listo (modelo=%s)", s.ollama_chat_model)

    yield


app = FastAPI(title="SGI-Agent API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health, chat, ingest, documents, history, compliance):
    app.include_router(r.router, prefix="/api")
