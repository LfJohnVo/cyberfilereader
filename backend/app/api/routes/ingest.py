import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.infrastructure.ingestion.pipeline import run_ingestion

router = APIRouter()
_lock = asyncio.Lock()
_last: dict = {"resumen": None}


async def _job(full: bool):
    async with _lock:
        _last["resumen"] = await asyncio.to_thread(run_ingestion, full)


@router.post("/ingest", status_code=202)
async def ingest(bg: BackgroundTasks, full: bool = Query(default=False)):
    if _lock.locked():
        raise HTTPException(409, "Ya hay una ingesta en curso.")
    bg.add_task(_job, full)
    return {"detail": "Ingesta iniciada", "full": full}


@router.get("/ingest/status")
async def ingest_status():
    return {"en_curso": _lock.locked(), "ultimo_resumen": _last["resumen"]}
