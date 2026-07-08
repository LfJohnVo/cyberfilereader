"""Rutas de historial de sesión."""

from fastapi import APIRouter

from app.services.memory import store as memory

router = APIRouter()


@router.get("/history/{session_id}")
async def history(session_id: str):
    return {
        "session_id": session_id,
        "messages": [{"role": r, "content": c} for r, c in memory.get_history(session_id)],
    }


@router.delete("/history/{session_id}", status_code=204)
async def clear_history(session_id: str):
    memory.clear(session_id)
