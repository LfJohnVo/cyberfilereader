import types

import pytest
from fastapi.testclient import TestClient

import app.main as main_mod
from app.services.rag.prompts import NO_INFO_MESSAGE


@pytest.fixture()
def container():
    """Contenedor falso: cada test define el `execute` de su caso de uso."""
    return types.SimpleNamespace(
        client=object(),
        vectorstore=object(),
        llm=object(),
        responder_consulta=types.SimpleNamespace(execute=None),
        evaluar_cumplimiento=types.SimpleNamespace(execute=None),
        ejecutar_agente=types.SimpleNamespace(execute=None),
    )


@pytest.fixture()
def client(monkeypatch, container):
    # El composition root se sustituye por el contenedor falso (DI = punto de inyección de prueba).
    monkeypatch.setattr(main_mod, "build_container", lambda: container)
    with TestClient(main_mod.app) as c:  # el 'with' dispara el lifespan
        yield c


def test_chat_ok(client, container):
    container.responder_consulta.execute = lambda *a, **k: {
        "answer": "Son 15 dias [1].",
        "sources": [
            {
                "n": 1,
                "file_name": "vacaciones_v2.txt",
                "source": "RRHH/Politicas/vacaciones_v2.txt",
                "area": "RRHH",
                "score": 0.8,
                "snippet": "15 dias habiles",
            }
        ],
        "no_info": False,
    }
    r = client.post(
        "/api/chat",
        json={"message": "¿vacaciones?", "session_id": "t1"},
        headers={"X-User-Areas": "RRHH"},
    )
    body = r.json()
    assert r.status_code == 200 and body["status"] == "idle" and body["sources"]


def test_chat_sin_cobertura(client, container):
    container.responder_consulta.execute = lambda *a, **k: {
        "answer": NO_INFO_MESSAGE,
        "sources": [],
        "no_info": True,
    }
    body = client.post(
        "/api/chat", json={"message": "capital de Australia", "session_id": "t1"}
    ).json()
    assert body["no_info"] is True and body["status"] == "no_info"


def test_backend_caido_devuelve_502(client, container):
    def boom(*a, **k):
        raise ConnectionError("ollama down")

    container.responder_consulta.execute = boom
    r = client.post("/api/chat", json={"message": "hola", "session_id": "t1"})
    assert r.status_code == 502
