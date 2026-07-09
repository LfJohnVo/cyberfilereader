import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import agent, chat, compliance, documents, health, history, ingest
from app.composition import build_container
from app.core.config import get_settings
from app.core.logging import setup_logging

s = get_settings()
setup_logging()
log = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        container = build_container()
    except Exception:
        log.exception(
            "No se pudo inicializar el contenedor (Qdrant/Ollama/colección); "
            "verifica QDRANT_URL, QDRANT_API_KEY, OLLAMA_BASE_URL y conectividad."
        )
        raise

    app.state.container = container
    app.state.qdrant = container.client  # compat con /health
    app.state.vectorstore = container.vectorstore  # compat
    app.state.llm = container.llm  # compat
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

for r in (health, chat, agent, ingest, documents, history, compliance):
    app.include_router(r.router, prefix="/api")
