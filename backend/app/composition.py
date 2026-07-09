"""Composition root: construye el grafo de objetos (adaptadores + casos de uso) en un solo lugar.

Es el ÚNICO punto donde se instancian los adaptadores concretos (Ollama/Qdrant). Las capas de
aplicación y presentación reciben las dependencias ya construidas; ninguna las crea por su cuenta.
"""

import logging
from dataclasses import dataclass

from app.application.casos_uso import EjecutarAgente, EvaluarCumplimiento, ResponderConsulta
from app.core.config import get_settings
from app.infrastructure.memory.store import InProcessMemory
from app.infrastructure.rag.embeddings import get_embeddings
from app.infrastructure.rag.llm import get_chat_model
from app.infrastructure.rag.vectorstore import (
    assert_schema,
    ensure_collection,
    get_client,
    get_vectorstore,
)

log = logging.getLogger(__name__)


@dataclass
class Container:
    client: object
    vectorstore: object
    llm: object
    memory: InProcessMemory
    responder_consulta: ResponderConsulta
    evaluar_cumplimiento: EvaluarCumplimiento
    ejecutar_agente: EjecutarAgente


def build_container() -> Container:
    s = get_settings()
    embeddings = get_embeddings()
    client = get_client()
    dim = len(embeddings.embed_query("probe"))
    ensure_collection(client, dim)
    assert_schema(client, dim)  # falla rápido ante dimensión/esquema incoherentes
    vectorstore = get_vectorstore(client, embeddings)
    llm = get_chat_model()
    memory = InProcessMemory()
    log.info("Contenedor construido (modelo=%s)", s.ollama_chat_model)
    return Container(
        client=client,
        vectorstore=vectorstore,
        llm=llm,
        memory=memory,
        responder_consulta=ResponderConsulta(llm, vectorstore, memory),
        evaluar_cumplimiento=EvaluarCumplimiento(llm, vectorstore),
        ejecutar_agente=EjecutarAgente(llm, vectorstore),
    )
