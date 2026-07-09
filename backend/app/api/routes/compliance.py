import asyncio
import logging
import os
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.deps import get_user_areas
from app.core.config import get_settings
from app.infrastructure.ingestion.loaders import load_file
from app.schemas.compliance import ComplianceResponse

log = logging.getLogger(__name__)
router = APIRouter()


def _guard_zip_bomb(path: Path, max_uncompressed_mb: int) -> None:
    # .docx/.xlsx son contenedores ZIP: valida el tamaño declarado antes de descomprimir (zip-bomb).
    if path.suffix.lower() not in (".docx", ".xlsx"):
        return
    try:
        with zipfile.ZipFile(path) as zf:
            total = sum(info.file_size for info in zf.infolist())
    except zipfile.BadZipFile:
        raise HTTPException(400, "Archivo comprimido inválido.") from None
    if total > max_uncompressed_mb * 1024 * 1024:
        raise HTTPException(400, f"El contenido descomprimido supera {max_uncompressed_mb} MB.")


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

    # El formulario solo puede acotar las áreas del usuario, nunca ampliarlas.
    requested = [a.strip() for a in areas_field.split(",") if a.strip()] if areas_field else None
    if not requested:
        target = user_areas
    elif user_areas is None or "*" in user_areas:
        target = requested
    elif all(a in user_areas for a in requested):
        target = requested
    else:
        raise HTTPException(403, "No tiene permiso sobre las áreas solicitadas.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)  # noqa: SIM115
    try:
        tmp.write(data)
        tmp.close()
        _guard_zip_bomb(Path(tmp.name), s.max_uncompressed_mb)
        docs = load_file(Path(tmp.name))
        text = "\n".join(d.page_content for d in docs)
    except HTTPException:
        raise
    except Exception:
        log.exception("Fallo extrayendo texto del archivo cargado")
        raise HTTPException(400, "No se pudo leer el contenido del archivo.") from None
    finally:
        try:
            os.unlink(tmp.name)
        except OSError as e:
            log.warning("No se pudo limpiar el archivo temporal %s: %s", tmp.name, e)

    uc = request.app.state.container.evaluar_cumplimiento
    try:
        result = await asyncio.to_thread(uc.execute, text, file.filename, target)
    except Exception:
        log.exception("Fallo en /compliance")
        raise HTTPException(502, "El agente no pudo evaluar el cumplimiento.") from None
    return result
