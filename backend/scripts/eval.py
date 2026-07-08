"""Evaluación de la recuperación — Fase 0 del plan de evolución RAG.

Mide la calidad de la recuperación con el MISMO camino que usa /chat (retriever.build_filter
+ búsqueda semántica), para tener un baseline antes de tocar reranking/híbrido, y para
recalibrar el umbral de score tras el cambio de modelo de embeddings.

Set dorado: backend/tests/eval/golden.json  (ver tests/eval/README.md).
Requiere Ollama + Qdrant alcanzables.

Uso (desde backend/, con el venv activo):
    python -m scripts.eval                 # métricas con la config actual (k, umbral)
    python -m scripts.eval --candidates 20 # nº de candidatos a recuperar por pregunta
    python -m scripts.eval --sweep         # barrido de umbral para recalibrarlo
"""

import argparse
import json
import sys
from pathlib import Path

from app.core.config import get_settings
from app.services.rag.embeddings import get_embeddings
from app.services.rag.retriever import build_filter, retrieve
from app.services.rag.vectorstore import get_client, get_vectorstore

# Consolas Windows (cp1252) no codifican acentos/símbolos: forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

GOLDEN = Path(__file__).resolve().parents[1] / "tests" / "eval" / "golden.json"


def _load_cases() -> list[dict]:
    if not GOLDEN.exists():
        return []
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    return [c for c in data.get("casos", []) if not str(c.get("id", "")).startswith("_")]


def _relevant(doc, expected: set[str]) -> bool:
    return doc.metadata.get("file_name") in expected


def _search_all(vs, cases: list[dict], candidates: int) -> list[tuple[dict, list]]:
    """Recupera candidatos SIN umbral (lo aplicamos en el análisis) una sola vez por caso."""
    out = []
    for c in cases:
        hits = vs.similarity_search_with_score(
            c["pregunta"], k=candidates, filter=build_filter(c.get("areas"))
        )
        out.append((c, hits))
    return out


def _report_current(per_case: list[tuple[dict, list]], k: int, thr: float, model: str) -> None:
    hit, mrr_sum = 0, 0.0
    for c, hits in per_case:
        expected = set(c.get("fuentes_esperadas", []))
        kept = [(d, sc) for d, sc in hits if sc >= thr][:k]
        ranks = [i for i, (d, _) in enumerate(kept, start=1) if _relevant(d, expected)]
        if ranks:
            hit += 1
            mrr_sum += 1 / ranks[0]
    n = len(per_case)
    print(f"Casos: {n} | k={k} | umbral={thr} | embeddings={model}")
    print(f"hit-rate@{k}: {hit / n:.1%}")
    print(f"MRR@{k}:      {mrr_sum / n:.3f}")


def _report_sweep(per_case: list[tuple[dict, list]], k: int) -> None:
    print("Barrido de umbral (recall = ≥1 fuente esperada sobrevive en el top-k):\n")
    print(f"{'umbral':>7} {'recall':>8} {'precisión':>10} {'frag/caso':>10}")
    best = (0.0, -1.0)
    for i in range(0, 95, 5):
        thr = i / 100
        recall_hits, kept_total, kept_rel = 0, 0, 0
        for c, hits in per_case:
            expected = set(c.get("fuentes_esperadas", []))
            kept = [(d, sc) for d, sc in hits if sc >= thr][:k]
            if any(_relevant(d, expected) for d, _ in kept):
                recall_hits += 1
            kept_total += len(kept)
            kept_rel += sum(1 for d, _ in kept if _relevant(d, expected))
        n = len(per_case)
        recall = recall_hits / n
        precision = (kept_rel / kept_total) if kept_total else 0.0
        # Heurística de "mejor umbral": prioriza recall, desempata por precisión.
        score = recall + precision * 0.25
        if score > best[1]:
            best = (thr, score)
        print(f"{thr:>7.2f} {recall:>8.1%} {precision:>10.1%} {kept_total / n:>10.1f}")
    print(f"\nSugerencia de SCORE_THRESHOLD ~ {best[0]:.2f} (recall maximo).")


def _report_pipeline(vs, cases: list[dict], s) -> None:
    """Evalúa el camino REAL de /chat (retrieve: umbral + reranking + top-k)."""
    hit, mrr_sum = 0, 0.0
    for c in cases:
        docs = retrieve(vs, c["pregunta"], c.get("areas"))
        expected = set(c.get("fuentes_esperadas", []))
        ranks = [
            i for i, (d, _) in enumerate(docs, start=1) if d.metadata.get("file_name") in expected
        ]
        if ranks:
            hit += 1
            mrr_sum += 1 / ranks[0]
    n = len(cases)
    rr = f"ON ({s.rerank_model})" if s.rerank_enabled else "OFF"
    print(f"[pipeline /chat] casos={n} k={s.retriever_k} umbral={s.score_threshold} rerank={rr}")
    print(f"hit-rate@{s.retriever_k}: {hit / n:.1%}")
    print(f"MRR@{s.retriever_k}:      {mrr_sum / n:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=int, default=20, help="candidatos por pregunta")
    ap.add_argument("--sweep", action="store_true", help="barrido de umbral para recalibrar")
    ap.add_argument("--pipeline", action="store_true", help="evalúa retrieve() real")
    args = ap.parse_args()

    cases = _load_cases()
    if not cases:
        print("Set dorado vacío. Rellena backend/tests/eval/golden.json (ver su README).")
        print("Tip: 'python -m scripts.check_collection' lista tus archivos/áreas reales.")
        return

    s = get_settings()
    vs = get_vectorstore(get_client(), get_embeddings())

    if args.pipeline:
        _report_pipeline(vs, cases, s)
        return

    per_case = _search_all(vs, cases, args.candidates)
    if args.sweep:
        _report_sweep(per_case, s.retriever_k)
    else:
        _report_current(per_case, s.retriever_k, s.score_threshold, s.ollama_embed_model)


if __name__ == "__main__":
    main()
