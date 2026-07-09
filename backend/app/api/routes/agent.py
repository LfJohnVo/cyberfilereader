"""Ruta POST /api/agent: orquestador con tools (búsqueda + cumplimiento).

Complementa a /chat (respuesta directa de un salto): el agente decide qué herramientas usar y
permite multi-salto. Más lento (varias llamadas al LLM), por eso es un endpoint aparte.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_user_areas
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent.graph import run_agent

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent", response_model=ChatResponse)
async def agent(
    body: ChatRequest, request: Request, areas: list[str] | None = Depends(get_user_areas)
):
    st = request.app.state
    try:
        result = await asyncio.to_thread(run_agent, st.llm, st.vectorstore, body.message, areas)
    except Exception:
        log.exception("Fallo en /agent")
        raise HTTPException(
            status_code=502, detail="El agente no pudo procesar la consulta."
        ) from None
    return ChatResponse(
        **result, session_id=body.session_id, status="no_info" if result["no_info"] else "idle"
    )
