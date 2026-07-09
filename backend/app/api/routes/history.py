"""Rutas de historial de sesión (usan la memoria inyectada en el contenedor)."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/history/{session_id}")
async def history(session_id: str, request: Request):
    memory = request.app.state.container.memory
    return {
        "session_id": session_id,
        "messages": [{"role": r, "content": c} for r, c in memory.get_history(session_id)],
    }


@router.delete("/history/{session_id}", status_code=204)
async def clear_history(session_id: str, request: Request):
    request.app.state.container.memory.clear(session_id)
