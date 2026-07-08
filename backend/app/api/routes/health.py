"""Ruta GET /api/health: estado de Qdrant y Ollama."""

import httpx
from fastapi import APIRouter, Request

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    s = get_settings()
    out = {"status": "ok", "qdrant": False, "ollama": False, "collection": s.qdrant_collection}
    try:
        out["qdrant"] = request.app.state.qdrant.collection_exists(s.qdrant_collection)
    except Exception as e:
        out["qdrant_error"] = str(e)[:200]
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{s.ollama_base_url}/api/tags")
            out["ollama"] = r.status_code == 200
    except Exception as e:
        out["ollama_error"] = str(e)[:200]
    if not (out["qdrant"] and out["ollama"]):
        out["status"] = "degraded"
    return out
