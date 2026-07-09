"""Juez LLM de fidelidad: ¿la respuesta se apoya en el contexto recuperado, sin inventar?

Para cada caso del set dorado: recupera contexto, genera la respuesta (mismo camino que
/chat) y un LLM juez puntúa la fidelidad 1-5. Da un número de calidad para vigilar en cada
cambio. Requiere Ollama + Qdrant.

Uso (desde backend/, con el venv):
    python -m scripts.eval_faithfulness            # muestra de 8 casos
    python -m scripts.eval_faithfulness --n 28     # todos
    python -m scripts.eval_faithfulness --ids sgi-001-mision,ens-002-codigo
"""

import argparse
import json
import re
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.infrastructure.memory.store import InProcessMemory
from app.infrastructure.rag.chain import answer_question
from app.infrastructure.rag.embeddings import get_embeddings
from app.infrastructure.rag.formatting import format_context
from app.infrastructure.rag.llm import get_chat_model, strip_reasoning
from app.infrastructure.rag.retriever import retrieve
from app.infrastructure.rag.vectorstore import get_client, get_vectorstore

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

GOLDEN = Path(__file__).resolve().parents[1] / "tests" / "eval" / "golden.json"

JUDGE_SYS = """Eres un evaluador ESTRICTO de fidelidad de respuestas RAG. Recibes un CONTEXTO
(fragmentos numerados) y una RESPUESTA. Decide si CADA afirmación de la respuesta está
respaldada por el contexto; no evalúes estilo ni completitud, solo si el contenido está
soportado. Devuelve SOLO un JSON válido, sin texto adicional:
{"fidelidad": <1-5>, "no_respaldadas": ["afirmacion", ...], "comentario": "<breve>"}
5 = todo respaldado; 3 = alguna afirmación menor sin respaldo; 1 = inventa información clave."""

JUDGE_USER = "CONTEXTO:\n{context}\n\nRESPUESTA:\n{answer}\n\nEvalúa la fidelidad (solo JSON)."


def _select(cases: list[dict], n: int, ids: str | None) -> list[dict]:
    cases = [c for c in cases if not str(c.get("id", "")).startswith("_")]
    if ids:
        wanted = {i.strip() for i in ids.split(",")}
        return [c for c in cases if c.get("id") in wanted]
    if n >= len(cases):
        return cases
    step = max(1, len(cases) // n)
    return cases[::step][:n]


def _parse(text: str) -> dict:
    text = strip_reasoning(text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:  # noqa: BLE001
            pass
    m = re.search(r'"?fidelidad"?\s*[:=]\s*([1-5])', text)
    return {
        "fidelidad": int(m.group(1)) if m else None,
        "no_respaldadas": [],
        "comentario": "parse-fallback",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--ids", type=str, default=None)
    args = ap.parse_args()

    get_settings()
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    cases = _select(data.get("casos", []), args.n, args.ids)

    llm = get_chat_model()
    vs = get_vectorstore(get_client(), get_embeddings())
    memory = InProcessMemory()

    scores: list[int] = []
    for i, c in enumerate(cases, 1):
        q, areas = c["pregunta"], c.get("areas")
        context, _ = format_context(retrieve(vs, q, areas))
        answer = answer_question(llm, vs, memory, q, f"faith-{i}", areas)["answer"]
        raw = llm.invoke(
            [
                SystemMessage(content=JUDGE_SYS),
                HumanMessage(content=JUDGE_USER.format(context=context, answer=answer)),
            ]
        ).content
        v = _parse(raw)
        f = v.get("fidelidad")
        if isinstance(f, int):
            scores.append(f)
        print(f"[{i}] fidelidad={f}  ·  {q[:62]}")
        if v.get("no_respaldadas"):
            print(f"      sin respaldo: {v['no_respaldadas']}")

    if scores:
        bajos = sum(1 for s in scores if s <= 3)
        media = sum(scores) / len(scores)
        print(f"\nFidelidad media: {media:.2f}/5  (n={len(scores)}, con fallos ≤3: {bajos})")


if __name__ == "__main__":
    main()
