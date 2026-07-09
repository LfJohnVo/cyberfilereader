import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_user_areas
from app.schemas.chat import ChatRequest, ChatResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agent", response_model=ChatResponse)
async def agent(
    body: ChatRequest, request: Request, areas: list[str] | None = Depends(get_user_areas)
):
    uc = request.app.state.container.ejecutar_agente
    try:
        result = await asyncio.to_thread(uc.execute, body.message, areas)
    except Exception:
        log.exception("Fallo en /agent")
        raise HTTPException(
            status_code=502, detail="El agente no pudo procesar la consulta."
        ) from None
    return ChatResponse(
        **result, session_id=body.session_id, status="no_info" if result["no_info"] else "idle"
    )
