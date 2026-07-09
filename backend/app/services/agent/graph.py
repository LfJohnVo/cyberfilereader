"""Agente con tools (LangGraph): orquesta búsqueda y cumplimiento sobre la documentación del SGI.

Reutiliza `retrieve()` y `assess_compliance()`; el LLM decide qué herramienta usar y en qué orden
(permite multi-salto). Acotado por `recursion_limit` para no bucear en un modelo local. Las tools
llevan `areas` en el cierre, de modo que respetan el control de acceso por área/estado.
"""

import logging

from langchain.agents import create_agent
from langchain_core.tools import tool

from app.services.rag.compliance import assess_compliance
from app.services.rag.formatting import to_source
from app.services.rag.llm import strip_reasoning
from app.services.rag.retriever import retrieve

log = logging.getLogger(__name__)

_AGENT_PROMPT = (
    "Eres SGI-Agent, asistente documental interno. Tu ÚNICA fuente de verdad es la documentación "
    "del SGI, a la que accedes mediante herramientas. Reglas: usa 'buscar_documentos' para "
    "responder consultas (puedes llamarla varias veces si la pregunta abarca varios temas o "
    "requiere comparar documentos); usa 'evaluar_cumplimiento' cuando el usuario aporte el texto "
    "de un documento a validar. Responde SOLO con lo que devuelvan las herramientas, cita las "
    "fuentes con [n], y si no hay información suficiente dilo con claridad. No inventes. Español."
)

_RECURSION_LIMIT = 8  # cota de pasos del agente (razona/llama-tool/observa)


def run_agent(llm, vectorstore, question: str, areas: list[str] | None) -> dict:
    """Ejecuta el agente sobre una consulta y devuelve {answer, sources, no_info}."""
    fuentes: list[dict] = []

    @tool
    def buscar_documentos(consulta: str) -> str:
        """Busca en la documentación VIGENTE del SGI (ISO, políticas, procedimientos, manuales) y
        devuelve fragmentos numerados con su fuente. Úsala para responder consultas del usuario."""
        hits = retrieve(vectorstore, consulta, areas)
        log.info("agent.buscar q=%.80s -> %d hits", consulta, len(hits))
        if not hits:
            return "SIN_RESULTADOS: no hay documentación vigente que cubra esa consulta."
        trozos = []
        for doc, score in hits:
            n = len(fuentes) + 1
            fuentes.append(to_source(n, doc, score))
            trozos.append(f"[{n}] {doc.metadata.get('file_name', '?')}: {doc.page_content[:400]}")
        return "\n\n".join(trozos)

    @tool
    def evaluar_cumplimiento(texto_documento: str, nombre: str) -> str:
        """Evalúa si el TEXTO de un documento cumple con las normas del SGI/ISO. Devuelve el
        veredicto (cumple/parcial/no_cumple) y el informe con hallazgos y recomendaciones."""
        log.info("agent.cumplimiento nombre=%s", nombre)
        r = assess_compliance(llm, vectorstore, texto_documento, nombre, areas)
        fuentes.extend(r.get("sources", []))
        return f"VEREDICTO: {r['verdict']}\n\n{r['report']}"

    agent = create_agent(
        llm, [buscar_documentos, evaluar_cumplimiento], system_prompt=_AGENT_PROMPT
    )
    out = agent.invoke(
        {"messages": [("user", question)]}, config={"recursion_limit": _RECURSION_LIMIT}
    )
    answer = strip_reasoning(out["messages"][-1].content or "")

    # Deduplica y renumera las fuentes acumuladas por todas las llamadas a las tools.
    vistos, dedup = set(), []
    for s in fuentes:
        clave = (s.get("file_name"), s.get("snippet"))
        if clave not in vistos:
            vistos.add(clave)
            dedup.append({**s, "n": len(dedup) + 1})
    return {"answer": answer, "sources": dedup, "no_info": not dedup}
