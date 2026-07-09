from langchain_core.documents import Document

from app.infrastructure.rag.crag import grade_context, rewrite_for_retry


class _FakeLLM:
    def __init__(self, out: str):
        self.out = out
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1

        class _R:
            content = self.out

        return _R()


class _BoomLLM:
    def invoke(self, _messages):
        raise RuntimeError("ollama caído")


_HITS = [(Document(page_content="las vacaciones son 15 días", metadata={}), 0.7)]


def test_grade_suficiente():
    assert grade_context(_FakeLLM("SI"), "¿cuántos días de vacaciones?", _HITS) is True


def test_grade_insuficiente():
    assert grade_context(_FakeLLM("NO, no lo cubre"), "¿el salario del CEO?", _HITS) is False


def test_grade_fail_open():
    # Fail-open: si el grader falla se asume suficiente.
    assert grade_context(_BoomLLM(), "x", _HITS) is True


def test_rewrite_devuelve_consulta():
    out = rewrite_for_retry(_FakeLLM("política de días de descanso"), "vacaciones")
    assert out == "política de días de descanso"


def test_rewrite_fallback():
    assert rewrite_for_retry(_BoomLLM(), "vacaciones") == "vacaciones"
