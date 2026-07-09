"""Servidor MCP de SGI-Agent: expone la recuperación documental como herramientas (tools).

Reutiliza el MISMO retriever que /chat (embeddings Ollama + filtro por área/estado + reranking),
así respeta el control de acceso y no duplica lógica. Pensado para que agentes o clientes MCP
(Cursor, el MCP Inspector u otros compatibles) consulten la documentación del SGI.

Ejecutar (desde cualquier ruta; se posiciona solo en backend/ para leer backend/.env):
    python mcp/server.py                                 # stdio (clientes locales)
    python mcp/server.py --transport http --port 8765    # red / agentes

Instalación: pip install -r mcp/requirements.txt
"""

import os
import sys
from functools import lru_cache
from pathlib import Path

# El servidor reutiliza el backend: nos posicionamos ahí para importar `app` y leer backend/.env.
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
os.chdir(_BACKEND)
sys.path.insert(0, str(_BACKEND))

from fastmcp import FastMCP  # noqa: E402  (tras ajustar sys.path/cwd)

mcp = FastMCP("SGI-Agent")


@lru_cache(maxsize=1)
def _vectorstore():
    from app.infrastructure.rag.embeddings import get_embeddings
    from app.infrastructure.rag.vectorstore import get_client, get_vectorstore

    return get_vectorstore(get_client(), get_embeddings())


@lru_cache(maxsize=1)
def _llm():
    from app.infrastructure.rag.llm import get_chat_model

    return get_chat_model()


def _evaluar_cumplimiento(texto: str, nombre: str, areas: list[str] | None) -> dict:
    from app.infrastructure.rag.compliance import assess_compliance

    return assess_compliance(_llm(), _vectorstore(), texto, nombre, areas)


def buscar_docs(query: str, areas: list[str] | None = None) -> list[dict]:
    from app.infrastructure.rag.retriever import retrieve

    hits = retrieve(_vectorstore(), query, areas)
    return [
        {
            "file_name": d.metadata.get("file_name"),
            "area": d.metadata.get("area"),
            "source": d.metadata.get("source"),
            "score": round(float(score), 3),
            "content": d.page_content,
        }
        for d, score in hits
    ]


def estado_coleccion() -> dict:
    from app.core.config import get_settings
    from app.infrastructure.rag.vectorstore import get_client

    s = get_settings()
    client = get_client()
    return {
        "coleccion": s.qdrant_collection,
        "fragmentos": client.count(s.qdrant_collection, exact=True).count,
        "modelo_embeddings": s.ollama_embed_model,
        "hibrido": s.hybrid_enabled,
    }


@mcp.tool
def sgi_buscar(query: str, areas: list[str] | None = None) -> list[dict]:
    """Busca en la documentación del SGI (ISO, políticas, procedimientos, manuales) y devuelve
    los fragmentos más relevantes con su fuente. 'areas' filtra por permiso/área (None o ["*"]
    = acceso total); solo se consideran documentos vigentes."""
    return buscar_docs(query, areas)


@mcp.tool
def sgi_estado() -> dict:
    """Estado de la base documental: colección, nº de fragmentos y modelo de embeddings."""
    return estado_coleccion()


@mcp.tool
def sgi_cumplimiento(ruta: str, areas: list[str] | None = None) -> dict:
    """Evalúa si el DOCUMENTO en 'ruta' (PDF, DOCX, TXT, MD, XLSX o CSV) cumple con las normas
    del SGI/ISO. Extrae el texto, recupera los requisitos aplicables y devuelve veredicto
    (cumple / parcial / no_cumple), informe con hallazgos y las fuentes citadas. 'areas' acota
    el área contra la que se evalúa (None = según permisos/todas)."""
    from pathlib import Path

    from app.infrastructure.ingestion.loaders import load_file

    p = Path(ruta)
    if not p.is_file():
        raise ValueError(f"No se encontró el archivo: {ruta}")
    texto = "\n".join(d.page_content for d in load_file(p))
    return _evaluar_cumplimiento(texto, p.name, areas)


@mcp.tool
def sgi_cumplimiento_texto(documento: str, nombre: str, areas: list[str] | None = None) -> dict:
    """Como sgi_cumplimiento pero recibe el TEXTO ya extraído del documento (útil en remoto o
    cuando el cliente ya tiene el contenido). 'nombre' identifica el documento en el informe."""
    return _evaluar_cumplimiento(documento, nombre, areas)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Servidor MCP de SGI-Agent")
    ap.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
