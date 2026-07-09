"""CRAG-lite: recuperación correctiva acotada.

Evalúa si el contexto recuperado basta para responder; si no, reformula la consulta y
reintenta UNA vez; si sigue sin bastar, se responde NO_INFO honesto en vez de arriesgar una
respuesta pobre. Coste: +1 evaluación por consulta (y +1 reintento solo si la primera falla).
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.rag.llm import strip_reasoning

log = logging.getLogger(__name__)

_GRADER_SYS = (
    "Eres un evaluador de relevancia. Dada una PREGUNTA y un CONTEXTO (fragmentos de "
    "documentos), responde SOLO con una palabra: 'SI' si el contexto contiene información "
    "suficiente para responder la pregunta, o 'NO' si no la cubre."
)

_REWRITE_SYS = (
    "Reescribe la CONSULTA de búsqueda para recuperar mejor: usa sinónimos y términos clave "
    "alternativos, y hazla algo más general si conviene. Responde SOLO con la consulta."
)


def grade_context(llm, question: str, hits) -> bool:
    """True si el contexto recuperado basta para responder la pregunta."""
    ctx = "\n\n".join(d.page_content[:600] for d, _ in hits[:5])
    prompt = f"PREGUNTA: {question}\n\nCONTEXTO:\n{ctx}\n\n¿Suficiente? (SI/NO):"
    try:
        out = strip_reasoning(
            llm.invoke([SystemMessage(content=_GRADER_SYS), HumanMessage(content=prompt)]).content
        )
        return not out.strip().upper().startswith("NO")
    except Exception:
        log.warning("Grader CRAG falló; se asume contexto suficiente", exc_info=True)
        return True  # fail-open: un fallo del grader no debe bloquear la respuesta


def rewrite_for_retry(llm, question: str) -> str:
    """Reescribe la consulta para un segundo intento de recuperación."""
    try:
        out = strip_reasoning(
            llm.invoke(
                [SystemMessage(content=_REWRITE_SYS), HumanMessage(content=question)]
            ).content
        )
        return out.strip().strip('"').splitlines()[0].strip() or question
    except Exception:
        log.warning("Reescritura CRAG falló; se usa la consulta original", exc_info=True)
        return question
