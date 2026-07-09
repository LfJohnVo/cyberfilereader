# Solo lectura sobre Qdrant.

import sys

from qdrant_client import models

from app.core.config import get_settings
from app.infrastructure.rag.vectorstore import get_client

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def main() -> None:
    s = get_settings()
    client = get_client()
    filt = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.estado", match=models.MatchValue(value="vigente")
            )
        ]
    )

    best: dict[str, tuple[str, str]] = {}
    offset = None
    while True:
        points, offset = client.scroll(
            s.qdrant_collection,
            scroll_filter=filt,
            with_payload=True,
            with_vectors=False,
            limit=256,
            offset=offset,
        )
        for p in points:
            pl = p.payload or {}
            md = pl.get("metadata", {})
            content = (pl.get("page_content") or "").strip()
            fn = md.get("file_name")
            if not fn or len(content) < 300:
                continue
            if fn not in best or len(content) > len(best[fn][1]):
                best[fn] = (md.get("area", "?"), content)
        if offset is None:
            break

    print(f"# {len(best)} documentos vigentes con contenido\n")
    for fn, (area, content) in sorted(best.items()):
        snippet = " ".join(content.split())[:380]
        print(f"### {fn}  [{area}]")
        print(snippet)
        print()


if __name__ == "__main__":
    main()
