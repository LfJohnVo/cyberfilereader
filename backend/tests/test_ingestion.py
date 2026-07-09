from qdrant_client import QdrantClient

from app.infrastructure.ingestion import pipeline
from tests.conftest import FakeEmbeddings


def _wire_inmemory(monkeypatch):
    # La pipeline importó las factorías en su namespace: se parchean AHÍ.
    client = QdrantClient(":memory:")
    monkeypatch.setattr(pipeline, "get_embeddings", lambda: FakeEmbeddings())
    monkeypatch.setattr(pipeline, "get_client", lambda: client)
    return client


def test_segunda_corrida_no_reindexa(docs_demo, monkeypatch):
    _wire_inmemory(monkeypatch)
    r1 = pipeline.run_ingestion()
    r2 = pipeline.run_ingestion()
    assert r1["indexados"] == 3 and r2["indexados"] == 0
    assert r2["sin_cambios"] == 3


def test_modificar_un_archivo_solo_reindexa_ese(docs_demo, monkeypatch):
    _wire_inmemory(monkeypatch)
    pipeline.run_ingestion()
    f = docs_demo / "RRHH" / "Politicas" / "vacaciones_v2.txt"
    f.write_text(f.read_text(encoding="utf-8") + " Ampliacion 2026.", encoding="utf-8")
    r = pipeline.run_ingestion()
    assert r["indexados"] == 1 and r["sin_cambios"] == 2


def test_borrado_en_disco_borra_del_indice(docs_demo, monkeypatch):
    _wire_inmemory(monkeypatch)
    pipeline.run_ingestion()
    (docs_demo / "Calidad" / "Procedimientos" / "auditorias_v1.txt").unlink()
    r = pipeline.run_ingestion()
    assert r["eliminados"] == 1
