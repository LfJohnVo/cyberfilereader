from app.infrastructure.memory.store import InProcessMemory


def test_maxlen_por_sesion():
    m = InProcessMemory(max_turns=2, max_sessions=10)
    for i in range(5):
        m.append("s", "user", str(i))
    assert m.get_history("s") == [("user", "3"), ("user", "4")]


def test_lru_acota_sesiones():
    m = InProcessMemory(max_turns=4, max_sessions=2)
    m.append("a", "user", "x")
    m.append("b", "user", "x")
    m.append("c", "user", "x")  # supera la cota -> se descarta la LRU ('a')
    assert m.get_history("a") == []
    assert m.get_history("b") and m.get_history("c")


def test_get_no_crea_sesion():
    m = InProcessMemory()
    assert m.get_history("inexistente") == []
    assert m.get_history("inexistente") == []
