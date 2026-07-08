from langchain_core.documents import Document

from app.services.rag.retriever import retrieve


def _seed(vs):
    vs.add_documents(
        [
            Document(
                page_content="politica de vacaciones quince dias",
                metadata={"area": "RRHH", "estado": "vigente", "source": "a"},
            ),
            Document(
                page_content="procedimiento de auditorias internas",
                metadata={"area": "Calidad", "estado": "vigente", "source": "b"},
            ),
            Document(
                page_content="politica de vacaciones version vieja",
                metadata={"area": "RRHH", "estado": "obsoleto", "source": "c"},
            ),
        ]
    )


def test_filtra_por_area_y_estado(mem_vectorstore):
    vs, _ = mem_vectorstore
    _seed(vs)
    hits = retrieve(vs, "politica de vacaciones", areas=["RRHH"])
    assert hits and all(d.metadata["area"] == "RRHH" for d, _ in hits)
    assert all(d.metadata["estado"] == "vigente" for d, _ in hits)  # el obsoleto NUNCA sale


def test_area_ajena_no_ve_nada(mem_vectorstore):
    vs, _ = mem_vectorstore
    _seed(vs)
    assert retrieve(vs, "politica de vacaciones", areas=["Operaciones"]) == []


def test_umbral_corta_lo_irrelevante(mem_vectorstore):
    vs, _ = mem_vectorstore
    _seed(vs)
    assert retrieve(vs, "resultado del mundial de futbol", areas=["*"]) == []
