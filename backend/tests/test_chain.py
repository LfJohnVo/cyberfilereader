from langchain_core.documents import Document

from app.infrastructure.memory.store import InProcessMemory
from app.infrastructure.rag.chain import answer_question
from app.infrastructure.rag.prompts import GREETING_MESSAGE, NO_INFO_MESSAGE


class _FakeLLM:
    def __init__(self, out: str = "Respuesta [1]."):
        self.out = out

    def invoke(self, _messages):
        class _R:
            content = self.out

        return _R()


def _seed(vs):
    vs.add_documents(
        [
            Document(
                page_content="politica de vacaciones quince dias habiles anuales",
                metadata={
                    "area": "RRHH",
                    "estado": "vigente",
                    "source": "a",
                    "file_name": "vac.pdf",
                },
            ),
        ]
    )


def test_saludo_no_busca(mem_vectorstore):
    vs, _ = mem_vectorstore
    r = answer_question(_FakeLLM(), vs, InProcessMemory(), "hola", "s1", ["*"])
    assert r["answer"] == GREETING_MESSAGE
    assert r["no_info"] is False
    assert r["sources"] == []


def test_pregunta_con_contexto(mem_vectorstore):
    vs, _ = mem_vectorstore
    _seed(vs)
    mem = InProcessMemory()
    r = answer_question(
        _FakeLLM("Son 15 dias [1]."), vs, mem, "politica de vacaciones", "s2", ["RRHH"]
    )
    assert r["no_info"] is False
    assert r["sources"] and r["sources"][0].file_name == "vac.pdf"
    assert len(mem.get_history("s2")) == 2


def test_sin_cobertura_no_info(mem_vectorstore):
    vs, _ = mem_vectorstore
    _seed(vs)
    r = answer_question(
        _FakeLLM(), vs, InProcessMemory(), "resultado del mundial de futbol", "s3", ["*"]
    )
    assert r["no_info"] is True
    assert r["answer"] == NO_INFO_MESSAGE
    assert r["sources"] == []
