"""Metadatos inferidos de la RUTA del archivo (guidelines §8)."""

import re
from datetime import UTC, datetime
from pathlib import Path

# Toma la última coincidencia de versión del nombre.
_VERSION_RE = re.compile(r"[ _\-]v\.?\s*(\d+(?:\.\d+)*)", re.IGNORECASE)


def infer_metadata(rel_path: Path, mtime: float) -> dict:
    parts = rel_path.parts
    upper_parts = [p.upper() for p in parts]
    area = parts[0] if len(parts) > 1 else "General"
    doc_type = parts[1] if len(parts) > 2 else rel_path.suffix.lstrip(".").upper()
    matches = _VERSION_RE.findall(rel_path.stem)
    version = matches[-1] if matches else "1"
    obsoleto = "OBSOLETOS" in upper_parts or "OBSOLETO" in rel_path.stem.upper()
    return {
        "source": rel_path.as_posix(),
        "file_name": rel_path.name,
        "area": area,
        "doc_type": doc_type,
        "version": version,
        "estado": "obsoleto" if obsoleto else "vigente",
        "fecha_modificacion": datetime.fromtimestamp(mtime, tz=UTC).isoformat(),
    }
