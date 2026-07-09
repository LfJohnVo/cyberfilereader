from app.infrastructure.rag.condense import _looks_dependent, condense_query


class _FakeLLM:
    def __init__(self, out: str = "REFORMULADA"):
        self.out = out
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1

        class _R:
            content = self.out

        return _R()


def test_sin_historial_no_reformula():
    llm = _FakeLLM()
    assert condense_query(llm, [], "¿y quién lo aprueba?") == "¿y quién lo aprueba?"
    assert llm.calls == 0


def test_pregunta_autonoma_larga_no_reformula():
    llm = _FakeLLM()
    q = "¿Cuáles son los tipos de escaneo de vulnerabilidades que se emplean en la metodología?"
    hist = [("user", "hola"), ("assistant", "hola")]
    assert condense_query(llm, hist, q) == q
    assert llm.calls == 0


def test_followup_dependiente_reformula():
    llm = _FakeLLM("¿Quién aprueba la política de protección de datos?")
    hist = [("user", "háblame de la política de datos"), ("assistant", "...")]
    out = condense_query(llm, hist, "¿y quién la aprueba?")
    assert out == "¿Quién aprueba la política de protección de datos?"
    assert llm.calls == 1


def test_fallback_si_llm_falla():
    class _Boom:
        def invoke(self, _m):
            raise RuntimeError("ollama caído")

    hist = [("user", "x"), ("assistant", "y")]
    assert condense_query(_Boom(), hist, "¿y eso?") == "¿y eso?"


def test_looks_dependent():
    assert _looks_dependent("¿y quién?")
    assert _looks_dependent("¿eso incluye las copias de seguridad diarias del sistema?")
    assert not _looks_dependent(
        "¿Qué controles de seguridad se aplican al instalar el sistema operativo en un equipo?"
    )
