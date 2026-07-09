from app.domain.ports import LlmPort, MemoryPort, VectorStorePort
from app.infrastructure.agent.graph import run_agent
from app.infrastructure.rag.chain import answer_question
from app.infrastructure.rag.compliance import assess_compliance


class ResponderConsulta:
    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort, memory: MemoryPort):
        self._llm = llm
        self._vectorstore = vectorstore
        self._memory = memory

    def execute(self, mensaje: str, session_id: str, areas: list[str] | None) -> dict:
        return answer_question(
            self._llm, self._vectorstore, self._memory, mensaje, session_id, areas
        )


class EvaluarCumplimiento:
    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort):
        self._llm = llm
        self._vectorstore = vectorstore

    def execute(self, texto: str, nombre: str, areas: list[str] | None) -> dict:
        return assess_compliance(self._llm, self._vectorstore, texto, nombre, areas)


class EjecutarAgente:
    def __init__(self, llm: LlmPort, vectorstore: VectorStorePort):
        self._llm = llm
        self._vectorstore = vectorstore

    def execute(self, mensaje: str, areas: list[str] | None) -> dict:
        return run_agent(self._llm, self._vectorstore, mensaje, areas)
