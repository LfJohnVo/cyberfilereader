"""Ruta POST /api/chat."""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_user_areas
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag.chain import answer_question

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, request: Request, areas: list[str] | None = Depends(get_user_areas)
):
    st = request.app.state
    try:
        result = await asyncio.to_thread(
            answer_question, st.llm, st.vectorstore, body.message, body.session_id, areas
        )
    except Exception:
        log.exception("Fallo en /chat")
        raise HTTPException(
            status_code=502,
            detail="El agente no pudo procesar la consulta (LLM o vector DB).",
        ) from None
    return ChatResponse(
        **result, session_id=body.session_id, status="no_info" if result["no_info"] else "idle"
    )
