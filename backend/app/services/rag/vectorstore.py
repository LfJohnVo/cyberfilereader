"""Cliente Qdrant compartido, creación idempotente de colección e índices de payload.

Soporta dos modos:
- Denso (por defecto): un vector denso sin nombre.
- Híbrido (HYBRID_ENABLED=true): vectores nombrados "dense" (Ollama) + "sparse" (BM25),
  fusionados con RRF. Requiere re-ingestar en una colección con este esquema.
"""

import logging

from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models

from app.core.config import get_settings
from app.services.rag.embeddings import get_sparse_embeddings

log = logging.getLogger(__name__)
_INDEXED_FIELDS = ["metadata.area", "metadata.estado", "metadata.source", "metadata.doc_type"]
_DENSE, _SPARSE = "dense", "sparse"  # nombres de vectores en modo híbrido


def get_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key, timeout=60)


def ensure_collection(client: QdrantClient, embed_dim: int) -> None:
    s = get_settings()
    if not client.collection_exists(s.qdrant_collection):
        if s.hybrid_enabled:
            client.create_collection(
                collection_name=s.qdrant_collection,
                vectors_config={
                    _DENSE: models.VectorParams(size=embed_dim, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={_SPARSE: models.SparseVectorParams()},
            )
        else:
            client.create_collection(
                collection_name=s.qdrant_collection,
                vectors_config=models.VectorParams(size=embed_dim, distance=models.Distance.COSINE),
            )
        log.info(
            "Colección '%s' creada (dim=%d, híbrida=%s)",
            s.qdrant_collection,
            embed_dim,
            s.hybrid_enabled,
        )
    for field in _INDEXED_FIELDS:  # necesarios para filtrar por área/estado en Cloud
        try:
            client.create_payload_index(
                s.qdrant_collection,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # ya existe


def get_vectorstore(client: QdrantClient, embeddings) -> QdrantVectorStore:
    s = get_settings()
    if s.hybrid_enabled:
        return QdrantVectorStore(
            client=client,
            collection_name=s.qdrant_collection,
            embedding=embeddings,
            sparse_embedding=get_sparse_embeddings(),
            retrieval_mode=RetrievalMode.HYBRID,
            vector_name=_DENSE,
            sparse_vector_name=_SPARSE,
        )
    return QdrantVectorStore(
        client=client, collection_name=s.qdrant_collection, embedding=embeddings
    )


def delete_by_source(client: QdrantClient, source: str) -> None:
    s = get_settings()
    client.delete(
        collection_name=s.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source", match=models.MatchValue(value=source)
                    )
                ]
            )
        ),
    )
