"""Metadatos (área, tipo, versión, estado) inferidos de la RUTA del archivo (guidelines §8).

Convención: docs/<AREA>/<TIPO?>/archivo.pdf. Carpeta o nombre OBSOLETO ⇒ estado=obsoleto.
Versión: detecta sufijos ` vN`, `_vN`, `-v.N`, `VN`, `V.N` (may/min) y toma la última coincidencia.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

# v/V opcionalmente precedida por espacio, guion o guion bajo, con punto opcional:
#   " v8", "_v2", "-v.1", " V11", "V.3"  ->  grupo = "8" / "2" / "1" / "11" / "3"
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
