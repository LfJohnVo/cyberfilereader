"""Ruta POST /api/compliance: evalúa el cumplimiento de un archivo cargado vs. el SGI/ISO."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.deps import get_user_areas
from app.core.config import get_settings
from app.infrastructure.ingestion.loaders import load_file
from app.schemas.compliance import ComplianceResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compliance", response_model=ComplianceResponse)
async def compliance(
    request: Request,
    file: UploadFile = File(...),
    areas_field: str | None = Form(default=None, alias="areas"),
    user_areas: list[str] | None = Depends(get_user_areas),
):
    s = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in s.extensions_set:
        raise HTTPException(400, f"Extensión no soportada: {ext}")
    data = await file.read()
    if len(data) > s.max_file_mb * 1024 * 1024:
        raise HTTPException(400, f"El archivo supera {s.max_file_mb} MB.")

    # Área objetivo: la del formulario si viene; si no, las del usuario (permisos).
    target = [a.strip() for a in areas_field.split(",") if a.strip()] if areas_field else user_areas

    # Extrae el texto en un archivo temporal (reutiliza los loaders de ingesta).
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)  # noqa: SIM115
    try:
        tmp.write(data)
        tmp.close()
        docs = load_file(Path(tmp.name))
        text = "\n".join(d.page_content for d in docs)
    except Exception:
        log.exception("Fallo extrayendo texto del archivo cargado")
        raise HTTPException(400, "No se pudo leer el contenido del archivo.") from None
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    uc = request.app.state.container.evaluar_cumplimiento
    try:
        result = await asyncio.to_thread(uc.execute, text, file.filename, target)
    except Exception:
        log.exception("Fallo en /compliance")
        raise HTTPException(502, "El agente no pudo evaluar el cumplimiento.") from None
    return result
