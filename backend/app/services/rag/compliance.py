"""Evalúa el cumplimiento de un documento cargado frente a los requisitos del SGI/ISO.

Reutiliza el retriever (mismos filtros de área/estado) para traer los requisitos aplicables
y pide al LLM un dictamen estructurado (veredicto + hallazgos + recomendaciones) con citas.
"""

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.domain.models import Veredicto
from app.services.rag.formatting import format_context
from app.services.rag.llm import strip_reasoning
from app.services.rag.prompts import COMPLIANCE_SYSTEM_PROMPT, COMPLIANCE_USER_TEMPLATE
from app.services.rag.retriever import retrieve

log = logging.getLogger(__name__)

_MAX_DOC_CHARS = 4500  # recorte del documento para no desbordar el contexto del LLM
_VERDICT_RE = re.compile(r"VEREDICTO:\s*(NO\s*CUMPLE|CUMPLE|PARCIAL)", re.IGNORECASE)


def _verdict(report: str) -> Veredicto:
    m = _VERDICT_RE.search(report)
    if not m:
        return Veredicto.INDETERMINADO
    key = m.group(1).upper().replace(" ", "")
    return {
        "CUMPLE": Veredicto.CUMPLE,
        "PARCIAL": Veredicto.PARCIAL,
        "NOCUMPLE": Veredicto.NO_CUMPLE,
    }.get(key, Veredicto.INDETERMINADO)


def assess_compliance(
    llm, vectorstore, doc_text: str, doc_name: str, areas: list[str] | None
) -> dict:
    doc = (doc_text or "").strip()
    if not doc:
        return {
            "file_name": doc_name,
            "verdict": Veredicto.INDETERMINADO,
            "report": "El documento no contiene texto extraíble (¿es un escaneo sin OCR?).",
            "sources": [],
        }

    # Recupera los requisitos del SGI aplicables usando el contenido del documento como consulta.
    hits = retrieve(vectorstore, doc[:1500], areas)
    if not hits:
        return {
            "file_name": doc_name,
            "verdict": Veredicto.INDETERMINADO,
            "report": (
                "No se encontraron requisitos del SGI aplicables para el área indicada. "
                "Prueba con otra área o confirma que el documento trate un tema del SGI."
            ),
            "sources": [],
        }

    requisitos, fuentes = format_context(hits)

    mensajes = [
        SystemMessage(content=COMPLIANCE_SYSTEM_PROMPT),
        HumanMessage(
            content=COMPLIANCE_USER_TEMPLATE.format(
                requisitos=requisitos,
                nombre=doc_name,
                documento=doc[:_MAX_DOC_CHARS],
            )
        ),
    ]
    log.info("compliance doc=%s areas=%s reqs=%d", doc_name, areas, len(hits))
    report = strip_reasoning(llm.invoke(mensajes).content)
    return {
        "file_name": doc_name,
        "verdict": _verdict(report),
        "report": report,
        "sources": fuentes,
    }
