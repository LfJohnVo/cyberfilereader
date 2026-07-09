"""Verificación de la colección Qdrant e inventario del corpus (SOLO LECTURA).

Fase 0 del plan de evolución RAG: confirma que la dimensión de la colección coincide
con el modelo de embeddings configurado y muestra el inventario de metadatos, útil para
construir el set dorado (backend/tests/eval/golden.json).

Uso (desde backend/, con el venv activo):
    python -m scripts.check_collection
"""

import logging
import sys
from collections import Counter

from app.core.config import get_settings
from app.infrastructure.rag.embeddings import get_embeddings
from app.infrastructure.rag.vectorstore import get_client

# Consolas Windows (cp1252) no codifican acentos/símbolos: forzamos UTF-8 y no reventamos.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

logging.basicConfig(level="WARNING", format="%(levelname)s %(name)s: %(message)s")


def _collection_dim(info) -> object:
    vectors = info.config.params.vectors
    if hasattr(vectors, "size"):  # vector denso único (sin nombre)
        return vectors.size
    if isinstance(vectors, dict):  # named vectors (p. ej. tras activar híbrido)
        return {name: params.size for name, params in vectors.items()}
    return "desconocida"


def main() -> None:
    s = get_settings()
    client = get_client()
    coll = s.qdrant_collection

    if not client.collection_exists(coll):
        print(f"[X] La coleccion '{coll}' no existe en {s.qdrant_url}")
        return

    info = client.get_collection(coll)
    coll_dim = _collection_dim(info)
    count = client.count(coll, exact=True).count

    print(f"Coleccion .......... {coll}")
    print(f"Puntos indexados ... {count}")
    print(f"Dimension coleccion  {coll_dim}")

    # Dimensión del modelo de embeddings actual (requiere Ollama alcanzable).
    try:
        embed_dim = len(get_embeddings().embed_query("probe"))
        print(f"Modelo embeddings .. {s.ollama_embed_model} -> {embed_dim} dim")
        if isinstance(coll_dim, int):
            if coll_dim == embed_dim:
                print("[OK] La dimension de la coleccion coincide con el modelo.")
            else:
                print(
                    f"[X] MISMATCH: coleccion={coll_dim} vs modelo={embed_dim}. "
                    "Recrear coleccion + re-ingestar (python -m scripts.ingest --full)."
                )
    except Exception as e:  # noqa: BLE001 — diagnóstico
        print(f"[!] No se pudo consultar Ollama en {s.ollama_base_url}: {e}")

    # Inventario de metadatos vía scroll (solo payload, sin vectores).
    areas, estados, dtypes, files = Counter(), Counter(), Counter(), Counter()
    offset = None
    while True:
        points, offset = client.scroll(
            coll, with_payload=True, with_vectors=False, limit=256, offset=offset
        )
        for p in points:
            md = (p.payload or {}).get("metadata", {})
            if md.get("area"):
                areas[md["area"]] += 1
            if md.get("estado"):
                estados[md["estado"]] += 1
            if md.get("doc_type"):
                dtypes[md["doc_type"]] += 1
            if md.get("file_name"):
                files[md["file_name"]] += 1
        if offset is None:
            break

    print(f"\nAreas ({len(areas)}): {dict(areas.most_common())}")
    print(f"Estados: {dict(estados)}")
    print(f"Tipos de documento: {dict(dtypes)}")
    print(f"\nArchivos indexados ({len(files)}):")
    for fn, c in files.most_common():
        print(f"  - {fn}  ({c} chunks)")


if __name__ == "__main__":
    main()
