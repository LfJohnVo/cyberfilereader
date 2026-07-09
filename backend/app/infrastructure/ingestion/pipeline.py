import json
import logging
import time
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.infrastructure.ingestion.loaders import load_file
from app.infrastructure.ingestion.metadata import infer_metadata
from app.infrastructure.rag.embeddings import get_embeddings
from app.infrastructure.rag.vectorstore import (
    assert_schema,
    delete_by_source,
    ensure_collection,
    get_client,
    get_vectorstore,
)
from app.utils.hashing import sha256_file

log = logging.getLogger(__name__)


def _manifest_path() -> Path:
    p = Path(get_settings().data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p / "manifest.json"


def _load_manifest() -> dict:
    p = _manifest_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_manifest(m: dict) -> None:
    tmp = _manifest_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_manifest_path())


def _iter_files(root: Path):
    s = get_settings()
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in s.extensions_set:
            continue
        if p.stat().st_size > s.max_file_mb * 1024 * 1024:
            log.warning("Omitido por tamaño (> %d MB): %s", s.max_file_mb, p.name)
            continue
        yield p


def run_ingestion(full: bool = False) -> dict:
    s = get_settings()
    root = Path(s.docs_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"DOCS_DIR no existe: {root}")

    t0 = time.time()
    embeddings = get_embeddings()
    dim = len(embeddings.embed_query("probe"))
    client = get_client()
    ensure_collection(client, dim)
    # Falla rápido antes de borrar/insertar si la colección no coincide con el modelo
    assert_schema(client, dim)
    vs = get_vectorstore(client, embeddings)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=s.chunk_size,
        chunk_overlap=s.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    manifest = {} if full else _load_manifest()
    vistos = set()
    resumen = {
        "indexados": 0,
        "sin_cambios": 0,
        "eliminados": 0,
        "chunks": 0,
        "vacios": [],
        "errores": [],
    }

    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        vistos.add(rel)
        try:
            digest = sha256_file(path)
            if manifest.get(rel, {}).get("sha256") == digest:
                resumen["sin_cambios"] += 1
                continue
            delete_by_source(client, rel)  # reindexar sin duplicar
            meta = infer_metadata(Path(rel), path.stat().st_mtime) | {"sha256": digest}
            docs = load_file(path)
            for d in docs:
                d.metadata = meta | d.metadata
            chunks = splitter.split_documents(docs)
            for i, c in enumerate(chunks):
                c.metadata["chunk"] = i
            if chunks:
                vs.add_documents(chunks)
                resumen["indexados"] += 1
                resumen["chunks"] += len(chunks)
                log.info("Indexado %s (%d chunks, estado=%s)", rel, len(chunks), meta["estado"])
            else:
                resumen["vacios"].append(rel)
                log.warning("Sin chunks (¿escaneo/vacío?): %s", rel)
            # Se actualiza siempre (incluso con 0 chunks) para no recargar en balde
            manifest[rel] = {
                "sha256": digest,
                "chunks": len(chunks),
                "estado": meta["estado"],
                "area": meta["area"],
            }
        except Exception as e:  # un archivo malo no frena la ingesta
            resumen["errores"].append({"archivo": rel, "error": str(e)})
            log.exception("Error ingiriendo %s", rel)

    for rel in [r for r in manifest if r not in vistos]:  # borrados del disco
        delete_by_source(client, rel)
        manifest.pop(rel)
        resumen["eliminados"] += 1

    _save_manifest(manifest)
    resumen["segundos"] = round(time.time() - t0, 1)
    return resumen
