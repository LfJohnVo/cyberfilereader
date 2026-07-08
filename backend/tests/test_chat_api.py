import pytest
from fastapi.testclient import TestClient

import app.main as main_mod
from app.api.routes import chat as chat_routes
from app.services.rag.prompts import NO_INFO_MESSAGE


@pytest.fixture()
def client(monkeypatch):
    # El lifespan crea clientes reales: se sustituyen las factorías EN main.
    monkeypatch.setattr(main_mod, "get_client", lambda: object())
    monkeypatch.setattr(main_mod, "get_embeddings", lambda: object())
    monkeypatch.setattr(main_mod, "get_vectorstore", lambda c, e: object())
    monkeypatch.setattr(main_mod, "get_chat_model", lambda: object())
    with TestClient(main_mod.app) as c:  # el 'with' dispara el lifespan
        yield c


def test_chat_ok(client, monkeypatch):
    monkeypatch.setattr(
        chat_routes,
        "answer_question",
        lambda llm, vs, q, session_id, areas: {
            "answer": "Son 15 dias habiles [1].",
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
        },
    )
    r = client.post(
        "/api/chat",
        json={"message": "¿vacaciones?", "session_id": "t1"},
        headers={"X-User-Areas": "RRHH"},
    )
    body = r.json()
    assert r.status_code == 200 and body["status"] == "idle" and body["sources"]


def test_chat_sin_cobertura(client, monkeypatch):
    monkeypatch.setattr(
        chat_routes,
        "answer_question",
        lambda *a, **k: {"answer": NO_INFO_MESSAGE, "sources": [], "no_info": True},
    )
    body = client.post(
        "/api/chat", json={"message": "capital de Australia", "session_id": "t1"}
    ).json()
    assert body["no_info"] is True and body["status"] == "no_info"


def test_backend_caido_devuelve_502(client, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("ollama down")

    monkeypatch.setattr(chat_routes, "answer_question", boom)
    r = client.post("/api/chat", json={"message": "hola", "session_id": "t1"})
    assert r.status_code == 502
