import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.domain.models import Veredicto
from app.infrastructure.rag.formatting import format_context
from app.infrastructure.rag.llm import strip_reasoning
from app.infrastructure.rag.prompts import COMPLIANCE_SYSTEM_PROMPT, COMPLIANCE_USER_TEMPLATE
from app.infrastructure.rag.retriever import retrieve

log = logging.getLogger(__name__)

_MAX_DOC_CHARS = 4500
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

    # Si se trunca, incumplimientos más allá del recorte podrían dar un falso CUMPLE.
    truncado = len(doc) > _MAX_DOC_CHARS
    if truncado:
        log.warning(
            "compliance: documento truncado doc=%s de %d a %d chars (dictamen solo del inicio)",
            doc_name,
            len(doc),
            _MAX_DOC_CHARS,
        )

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
    log.info("compliance doc=%s areas=%s reqs=%d chars=%d", doc_name, areas, len(hits), len(doc))
    report = strip_reasoning(llm.invoke(mensajes).content)
    verdict = _verdict(report)
    if truncado:
        report = (
            f"[AVISO: documento truncado a {_MAX_DOC_CHARS} de {len(doc)} caracteres; "
            "el dictamen cubre solo el inicio del documento.]\n\n" + report
        )
    return {
        "file_name": doc_name,
        "verdict": verdict,
        "report": report,
        "sources": fuentes,
    }
