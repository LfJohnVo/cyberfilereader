"""Orquesta: memoria → retrieve (filtrado) → prompt con fuentes numeradas → LLM.

Devuelve respuesta + fuentes estructuradas + bandera no_info. Función síncrona a
propósito: las rutas la ejecutan con asyncio.to_thread para no bloquear el event loop.
"""

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.config import get_settings
from app.services.memory import store as memory
from app.services.rag.condense import condense_query
from app.services.rag.llm import strip_reasoning
from app.services.rag.prompts import (
    GREETING_MESSAGE,
    NO_INFO_MESSAGE,
    SYSTEM_PROMPT,
    USER_TEMPLATE,
)
from app.services.rag.retriever import retrieve

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


def _format_context(hits) -> tuple[str, list[dict]]:
    bloques, fuentes = [], []
    for n, (doc, score) in enumerate(hits, start=1):
        m = doc.metadata
        ubic = (
            f", pág. {m['page']}"
            if m.get("page")
            else (f", hoja {m['sheet']}" if m.get("sheet") else "")
        )
        bloques.append(f"[{n}] ({m['file_name']} — área {m['area']}{ubic})\n{doc.page_content}")
        fuentes.append(
            {
                "n": n,
                "file_name": m["file_name"],
                "source": m["source"],
                "area": m["area"],
                "doc_type": m.get("doc_type"),
                "version": m.get("version"),
                "page": m.get("page"),
                "score": round(float(score), 3),
                "snippet": doc.page_content[:220],
            }
        )
    return "\n\n".join(bloques), fuentes


def answer_question(
    llm, vectorstore, question: str, session_id: str, areas: list[str] | None
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

    hits = retrieve(vectorstore, search_q, areas)
    if not hits:
        memory.append(session_id, "user", question)
        memory.append(session_id, "assistant", NO_INFO_MESSAGE)
        return {"answer": NO_INFO_MESSAGE, "sources": [], "no_info": True}

    context, fuentes = _format_context(hits)
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
