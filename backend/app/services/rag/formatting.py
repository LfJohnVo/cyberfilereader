"""Formateo compartido de fuentes y bloques de contexto (chat y cumplimiento).

Fuente única del contrato Source y de los bloques numerados [n]; consumido por chain.py y
compliance.py para no duplicar (ni divergir) el formato.
"""

from langchain_core.documents import Document

from app.domain.models import Fuente


def _ubicacion(m: dict) -> str:
    if m.get("page"):
        return f", pág. {m['page']}"
    if m.get("sheet"):
        return f", hoja {m['sheet']}"
    return ""


def to_source(n: int, doc: Document, score: float) -> Fuente:
    m = doc.metadata
    return Fuente(
        n=n,
        file_name=m.get("file_name", "?"),
        source=m.get("source", ""),
        area=m.get("area", "?"),
        doc_type=m.get("doc_type"),
        version=m.get("version"),
        page=m.get("page"),
        score=round(float(score), 3),
        snippet=doc.page_content[:220],
    )


def format_context(hits: list[tuple[Document, float]]) -> tuple[str, list[Fuente]]:
    """Devuelve (contexto numerado [n], lista de Fuente) para el prompt y la respuesta."""
    bloques, fuentes = [], []
    for n, (doc, score) in enumerate(hits, start=1):
        m = doc.metadata
        cab = f"[{n}] ({m.get('file_name', '?')} — área {m.get('area', '?')}{_ubicacion(m)})"
        bloques.append(f"{cab}\n{doc.page_content}")
        fuentes.append(to_source(n, doc, score))
    return "\n\n".join(bloques), fuentes
