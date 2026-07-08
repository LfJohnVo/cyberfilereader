"""Genera respuestas REALES del chain (retrieve + LLM) para diagnosticar la generación.

Ejecuta el mismo camino que /chat sobre una muestra del set dorado e imprime pregunta,
respuesta y fuentes, para revisar a ojo la calidad de la redacción y las citas.

Uso (desde backend/, con el venv):
    python -m scripts.answer_sample                 # muestra distribuida (6 casos)
    python -m scripts.answer_sample --n 8
    python -m scripts.answer_sample --ids sgi-001-mision,ens-002-codigo
"""

import argparse
import json
import sys
from pathlib import Path

from app.core.config import get_settings
from app.services.rag.chain import answer_question
from app.services.rag.embeddings import get_embeddings
from app.services.rag.llm import get_chat_model
from app.services.rag.vectorstore import get_client, get_vectorstore

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

GOLDEN = Path(__file__).resolve().parents[1] / "tests" / "eval" / "golden.json"


def _select(cases: list[dict], n: int, ids: str | None) -> list[dict]:
    cases = [c for c in cases if not str(c.get("id", "")).startswith("_")]
    if ids:
        wanted = {i.strip() for i in ids.split(",")}
        return [c for c in cases if c.get("id") in wanted]
    if n >= len(cases):
        return cases
    step = max(1, len(cases) // n)  # muestreo por saltos = variedad de áreas
    return cases[::step][:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--ids", type=str, default=None)
    args = ap.parse_args()

    get_settings()
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    cases = _select(data.get("casos", []), args.n, args.ids)

    llm = get_chat_model()
    vs = get_vectorstore(get_client(), get_embeddings())

    for i, c in enumerate(cases, 1):
        res = answer_question(llm, vs, c["pregunta"], f"diag-{i}", c.get("areas"))
        print("=" * 88)
        print(f"P{i}: {c['pregunta']}")
        print(f"    esperado: {c.get('fuentes_esperadas')}  | no_info={res['no_info']}")
        print("-" * 88)
        print(res["answer"])
        print("  · fuentes:", [s["file_name"] for s in res["sources"]])
        print()


if __name__ == "__main__":
    main()
