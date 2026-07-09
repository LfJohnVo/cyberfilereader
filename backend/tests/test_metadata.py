from pathlib import Path

from app.infrastructure.ingestion.metadata import infer_metadata


def test_area_tipo_y_version():
    m = infer_metadata(Path("RRHH/Politicas/vacaciones_v2.txt"), mtime=0.0)
    assert (m["area"], m["doc_type"], m["version"], m["estado"]) == (
        "RRHH",
        "Politicas",
        "2",
        "vigente",
    )


def test_obsoleto_por_carpeta_y_por_nombre():
    assert infer_metadata(Path("RRHH/Politicas/OBSOLETOS/x_v1.txt"), 0)["estado"] == "obsoleto"
    assert infer_metadata(Path("Calidad/Manuales/manual_OBSOLETO.pdf"), 0)["estado"] == "obsoleto"


def test_archivo_suelto_en_raiz():
    m = infer_metadata(Path("aviso.txt"), 0)
    assert m["area"] == "General" and m["version"] == "1"


def test_version_con_espacio_guion_y_mayuscula():
    # Formatos reales del corpus: " v8", "_V3", "-v.1", "V.3"
    assert infer_metadata(Path("Talento/M-GET-012 Manual v8.pdf"), 0)["version"] == "8"
    assert infer_metadata(Path("Auto/M-AUT-001 Seguridad_V3.pdf"), 0)["version"] == "3"
    assert infer_metadata(Path("Cib/M-SGI-008-Metodologia BIA-v.1.pdf"), 0)["version"] == "1"
    assert infer_metadata(Path("Obsoletos/M-GET-012 TALENTO V.3.pdf"), 0)["version"] == "3"
