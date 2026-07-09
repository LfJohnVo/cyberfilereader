from app.services.rag.compliance import _verdict


def test_verdict_cumple():
    assert _verdict("VEREDICTO: CUMPLE\nEl documento satisface...") == "cumple"


def test_verdict_parcial():
    assert _verdict("VEREDICTO: PARCIAL — cumple algunos requisitos") == "parcial"


def test_verdict_no_cumple():
    assert _verdict("VEREDICTO: NO CUMPLE. Faltan controles.") == "no_cumple"
    assert _verdict("VEREDICTO: NOCUMPLE") == "no_cumple"


def test_verdict_case_insensitive():
    assert _verdict("veredicto: no cumple") == "no_cumple"


def test_verdict_ausente_indeterminado():
    assert _verdict("El documento parece razonable, sin línea de veredicto.") == "indeterminado"
