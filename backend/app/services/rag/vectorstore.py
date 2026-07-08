"""Cliente Qdrant compartido, creación idempotente de colección e índices de payload."""

import logging

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from app.core.config import get_settings

log = logging.getLogger(__name__)
_INDEXED_FIELDS = ["metadata.area", "metadata.estado", "metadata.source", "metadata.doc_type"]


def get_client() -> QdrantClient:
    s = get_settings()
    return QdrantClient(url=s.qdrant_url, api_key=s.qdrant_api_key, timeout=60)


def ensure_collection(client: QdrantClient, embed_dim: int) -> None:
    s = get_settings()
    if not client.collection_exists(s.qdrant_collection):
        client.create_collection(
            collection_name=s.qdrant_collection,
            vectors_config=models.VectorParams(size=embed_dim, distance=models.Distance.COSINE),
        )
        log.info("Colección '%s' creada (dim=%d)", s.qdrant_collection, embed_dim)
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
