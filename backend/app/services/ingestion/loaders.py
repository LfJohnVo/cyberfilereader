"""Extrae texto de PDF, DOCX, TXT, MD, XLSX y CSV como lista de Documents.

Cada loader es una función pura: sin red, sin estado, fácil de testear.
"""

import logging
from pathlib import Path

import docx2txt
import pandas as pd
from langchain_core.documents import Document
from pypdf import PdfReader

log = logging.getLogger(__name__)


def _pdf(path: Path) -> list[Document]:
    out = []
    for i, page in enumerate(PdfReader(str(path)).pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            out.append(Document(page_content=text, metadata={"page": i}))
    if not out:  # PDF escaneado sin capa de texto (OCR fuera de alcance)
        log.warning("PDF sin texto extraíble (¿escaneo?): %s", path.name)
    return out


def _docx(path: Path) -> list[Document]:
    text = (docx2txt.process(str(path)) or "").strip()
    return [Document(page_content=text)] if text else []


def _texto(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    return [Document(page_content=text)] if text else []


def _tabular(df: pd.DataFrame, origen: str) -> str:
    df = df.dropna(how="all").fillna("")
    return f"[{origen}]\n" + df.to_csv(sep="|", index=False)


def _xlsx(path: Path) -> list[Document]:
    hojas = pd.read_excel(path, sheet_name=None, dtype=str)
    return [
        Document(page_content=_tabular(df, f"Hoja: {nombre}"), metadata={"sheet": nombre})
        for nombre, df in hojas.items()
        if not df.dropna(how="all").empty
    ]


def _csv(path: Path) -> list[Document]:
    df = pd.read_csv(path, dtype=str)
    return [Document(page_content=_tabular(df, path.name))] if not df.empty else []


LOADERS = {
    ".pdf": _pdf,
    ".docx": _docx,
    ".txt": _texto,
    ".md": _texto,
    ".xlsx": _xlsx,
    ".csv": _csv,
}


def load_file(path: Path) -> list[Document]:
    loader = LOADERS.get(path.suffix.lower())
    if loader is None:
        raise ValueError(f"Extensión no soportada: {path.suffix}")
    return loader(path)
