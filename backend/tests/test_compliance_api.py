"""Autorización por área en POST /api/compliance: el campo `areas` del formulario puede ACOTAR
a un subconjunto de los permisos del usuario, nunca ampliarlos (regresión del bypass de filtro)."""

import types

import pytest
from fastapi.testclient import TestClient

import app.main as main_mod

_OK = {"file_name": "doc.txt", "verdict": "cumple", "report": "VEREDICTO: CUMPLE", "sources": []}


@pytest.fixture()
def container():
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
    monkeypatch.setattr(main_mod, "build_container", lambda: container)
    with TestClient(main_mod.app) as c:  # el 'with' dispara el lifespan
        yield c


def _upload(client, areas: str, user_areas: str, spy):
    client.app.state.container.evaluar_cumplimiento.execute = spy
    return client.post(
        "/api/compliance",
        files={"file": ("doc.txt", b"contenido de prueba", "text/plain")},
        data={"areas": areas},
        headers={"X-User-Areas": user_areas},
    )


def test_rechaza_area_no_autorizada(client):
    """Usuario de 'Calidad' pide 'Direccion' -> 403 y NO se evalúa nada."""
    llamado = {"target": "no-llamado"}

    def spy(text, name, target):
        llamado["target"] = target
        return _OK

    r = _upload(client, areas="Direccion", user_areas="Calidad", spy=spy)
    assert r.status_code == 403
    assert llamado["target"] == "no-llamado"


def test_acota_a_subconjunto_permitido(client):
    """Usuario de 'Calidad,RRHH' pide 'Calidad' -> 200 y evalúa solo sobre ['Calidad']."""
    capt = {}

    def spy(text, name, target):
        capt["target"] = target
        return _OK

    r = _upload(client, areas="Calidad", user_areas="Calidad,RRHH", spy=spy)
    assert r.status_code == 200
    assert capt["target"] == ["Calidad"]


def test_perfil_total_puede_pedir_cualquier_area(client):
    """Perfil '*' (acceso total) sí puede acotar a un área arbitraria -> 200."""
    capt = {}

    def spy(text, name, target):
        capt["target"] = target
        return _OK

    r = _upload(client, areas="Direccion", user_areas="*", spy=spy)
    assert r.status_code == 200
    assert capt["target"] == ["Direccion"]
