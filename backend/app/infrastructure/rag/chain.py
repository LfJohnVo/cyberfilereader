"""Orquesta: memoria → retrieve (filtrado) → prompt con fuentes numeradas → LLM.

Devuelve respuesta + fuentes estructuradas + bandera no_info. Función síncrona a
propósito: las rutas la ejecutan con asyncio.to_thread para no bloquear el event loop.
"""

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.config import get_settings
from app.domain.ports import MemoryPort
from app.infrastructure.rag.condense import condense_query
from app.infrastructure.rag.crag import grade_context, rewrite_for_retry
from app.infrastructure.rag.formatting import format_context
from app.infrastructure.rag.llm import strip_reasoning
from app.infrastructure.rag.prompts import (
    GREETING_MESSAGE,
    NO_INFO_MESSAGE,
    SYSTEM_PROMPT,
    USER_TEMPLATE,
)
from app.infrastructure.rag.retriever import search

log = logging.getLogger(__name__)

# Saludos/cortesía: se responden de forma conversacional (no disparan RAG ni NO_INFO).
_GREETING_RE = re.compile(
    r"^\s*(hola+|holi|buen[oa]s?(\s+(d[ií]as|tardes|noches))?|qu[eé]\s+tal|q'?\s?onda|"
    r"hey+|hi+|hello|saludos|buenas)\b",
    re.IGNORECASE,
)


def _is_greeting(text: str) -> bool:
    s = text.strip()
    return len(s) <= 40 and bool(_GREETING_RE.match(s))


def answer_question(
    llm, vectorstore, memory: MemoryPort, question: str, session_id: str, areas: list[str] | None
) -> dict:
    # Saludo/cortesía: responde amablemente sin buscar en la documentación.
    if _is_greeting(question):
        memory.append(session_id, "user", question)
        memory.append(session_id, "assistant", GREETING_MESSAGE)
        return {"answer": GREETING_MESSAGE, "sources": [], "no_info": False}

    # Reformula follow-ups con el historial para recuperar mejor (la generación ve el historial).
    history = memory.get_history(session_id)
    search_q = question
    if get_settings().condense_enabled:
        search_q = condense_query(llm, history, question)
        if search_q != question:
            log.info("condense sid=%s: %.100s -> %.100s", session_id, question, search_q)

    hits = search(vectorstore, search_q, areas).hits

    # CRAG-lite: el grader juzga con search_q (la consulta que recuperó los hits), no la cruda.
    if get_settings().crag_enabled and hits and not grade_context(llm, search_q, hits):
        alt_q = rewrite_for_retry(llm, search_q)
        alt_hits = search(vectorstore, alt_q, areas).hits
        if alt_hits and grade_context(llm, search_q, alt_hits):
            hits = alt_hits
            log.info("CRAG sid=%s: reintento útil (%.80s)", session_id, alt_q)
        else:
            log.info("CRAG sid=%s: contexto insuficiente -> NO_INFO", session_id)
            hits = []

    if not hits:
        memory.append(session_id, "user", question)
        memory.append(session_id, "assistant", NO_INFO_MESSAGE)
        return {"answer": NO_INFO_MESSAGE, "sources": [], "no_info": True}

    context, fuentes = format_context(hits)
    mensajes: list = [SystemMessage(content=SYSTEM_PROMPT)]
    for role, content in history:
        mensajes.append(
            HumanMessage(content=content) if role == "user" else AIMessage(content=content)
        )
    mensajes.append(HumanMessage(content=USER_TEMPLATE.format(context=context, question=question)))

    log.info("chat sid=%s areas=%s q=%.300s", session_id, areas, question)
    respuesta = strip_reasoning(llm.invoke(mensajes).content)

    memory.append(session_id, "user", question)
    memory.append(session_id, "assistant", respuesta)
    return {"answer": respuesta, "sources": fuentes, "no_info": False}
