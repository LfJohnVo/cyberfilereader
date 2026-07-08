"""Rutas de documentos y áreas indexadas (leen el manifiesto de ingesta)."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.deps import get_user_areas
from app.core.config import get_settings
from app.schemas.documents import AreasResponse, DocumentsResponse

router = APIRouter()


@router.get("/documents", response_model=DocumentsResponse)
async def documents(areas: list[str] | None = Depends(get_user_areas)):
    p = Path(get_settings().data_dir) / "manifest.json"
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    items = [
        {"source": k, **v}
        for k, v in data.items()
        if areas == ["*"] or v.get("area") in (areas or [])
    ]
    return {"total": len(items), "items": sorted(items, key=lambda x: x["source"])}


@router.get("/areas", response_model=AreasResponse)
async def areas_disponibles():
    p = Path(get_settings().data_dir) / "manifest.json"
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return {"areas": sorted({v.get("area") for v in data.values() if v.get("area")})}
