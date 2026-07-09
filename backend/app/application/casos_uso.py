"""Casos de uso (capa de aplicación).

Cada caso de uso recibe sus dependencias por constructor (puertos), no las construye ni lee
`get_settings()`. Por ahora delegan en las funciones de servicio existentes (strangler); la lógica
interna se irá moviendo aquí en incrementos posteriores.
"""

from app.domain.ports import LlmPort, VectorStorePort
from app.services.agent.graph import run_agent
from app.services.rag.chain import answer_question
from app.services.rag.compliance import assess_compliance


class ResponderConsulta:
    """Oráculo documental de un salto: recupera contexto y responde con citas (o NO_INFO)."""

    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort):
        self._llm = llm
        self._vectorstore = vectorstore

    def execute(self, mensaje: str, session_id: str, areas: list[str] | None) -> dict:
        return answer_question(self._llm, self._vectorstore, mensaje, session_id, areas)


class EvaluarCumplimiento:
    """Evalúa si el texto de un documento cumple con las normas del SGI/ISO."""

    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort):
        self._llm = llm
        self._vectorstore = vectorstore

    def execute(self, texto: str, nombre: str, areas: list[str] | None) -> dict:
        return assess_compliance(self._llm, self._vectorstore, texto, nombre, areas)


class EjecutarAgente:
    """Agente con tools (búsqueda + cumplimiento); permite multi-salto."""

    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort):
        self._llm = llm
        self._vectorstore = vectorstore

    def execute(self, mensaje: str, areas: list[str] | None) -> dict:
        return run_agent(self._llm, self._vectorstore, mensaje, areas)
