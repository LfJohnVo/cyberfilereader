# Set dorado y evaluación de recuperación (Fase 0)

Base de medición para no evolucionar el RAG "a ciegas": mide la calidad de la
recuperación **antes y después** de cada mejora (reranking, híbrido, etc.).

## 1. Inventariar el corpus real
Desde `backend/` con el venv activo:

```bash
python -m scripts.check_collection
```

Verifica que la dimensión de la colección coincide con `qwen3-embedding:8b` y lista
tus **áreas** y **archivos** reales (los `file_name` que irán en `fuentes_esperadas`).

## 2. Rellenar `golden.json`
Cada caso:

| campo | qué es |
|---|---|
| `id` | identificador libre (los que empiezan por `_` se ignoran) |
| `pregunta` | pregunta real de un usuario |
| `tipo` | `single-hop` \| `multi-hop` \| `follow-up` \| `codigo-clausula` |
| `areas` | `null` (acceso total, filtra solo `estado=vigente`), o lista de áreas, o `["*"]` |
| `fuentes_esperadas` | lista de `file_name` que DEBERÍAN recuperarse para responder |

Meta: **25–40 casos** variados. Cuantos más y más representativos, mejor la señal.

## 3. Medir baseline y recalibrar el umbral

```bash
python -m scripts.eval            # hit-rate@k y MRR con la config actual
python -m scripts.eval --sweep    # barrido de SCORE_THRESHOLD -> valor sugerido
```

- **hit-rate@k**: % de casos en los que al menos una `fuente_esperada` aparece en el top-k.
- **MRR**: qué tan arriba aparece la primera fuente esperada (1.0 = siempre la primera).
- `--sweep`: como el `0.65` estaba calibrado para `nomic-embed-text`, este barrido sugiere
  el `SCORE_THRESHOLD` adecuado para `qwen3-embedding:8b`. Ajusta el valor en `.env`,
  `.env.example`, `config.py` y la tabla del `README.md`.

Guarda los números en `docs-proyecto/plans/eval-baseline.md` para comparar tras cada fase.
