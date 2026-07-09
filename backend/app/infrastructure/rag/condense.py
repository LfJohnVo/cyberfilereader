"""Reformulación de la consulta con el historial (follow-ups).

Convierte un seguimiento dependiente del contexto ("¿y quién lo aprueba?") en una pregunta
autónoma, SOLO para recuperar mejor; la generación sigue viendo el historial completo. Una
heurística evita la llamada extra al LLM cuando la pregunta ya es autónoma.
"""

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.infrastructure.rag.llm import strip_reasoning

log = logging.getLogger(__name__)

# Señales de dependencia del contexto previo (evita artículos comunes como "la/lo").
_DEP_RE = re.compile(
    r"(^\s*¿?\s*y\s)|"
    r"\b(eso|esa|ese|esos|esas|aquel|aquella|aquello|ah[ií]|all[ií]|anterior|previa|previo|"
    r"mism[oa]|tambi[eé]n|tampoco|entonces|dich[oa]|al respecto)\b",
    re.IGNORECASE,
)

_SYS = (
    "Reformula la PREGUNTA como una consulta autónoma y completa, resolviendo referencias al "
    "HISTORIAL (pronombres, 'eso', 'el anterior', etc.). Conserva idioma e intención. Si ya es "
    "autónoma, devuélvela igual. Responde SOLO con la pregunta, sin comillas ni explicación."
)


def _looks_dependent(q: str) -> bool:
    """True si la pregunta parece depender del contexto previo (corta o con anáfora)."""
    return len(q.strip()) < 60 or bool(_DEP_RE.search(q))


def condense_query(llm, history: list[tuple[str, str]], question: str) -> str:
    """Devuelve una consulta autónoma para recuperar; la original si no hace falta reformular."""
    if not history or not _looks_dependent(question):
        return question
    hist = "\n".join(
        f"{'Usuario' if role == 'user' else 'Asistente'}: {content}"
        for role, content in history
    )
    prompt = f"HISTORIAL:\n{hist}\n\nPREGUNTA: {question}\n\nConsulta autónoma:"
    try:
        raw = strip_reasoning(
            llm.invoke([SystemMessage(content=_SYS), HumanMessage(content=prompt)]).content
        )
        out = raw.strip().strip('"').splitlines()[0].strip() if raw else ""
        return out or question
    except Exception:
        log.warning("Fallo al reformular la consulta; se usa la original", exc_info=True)
        return question
