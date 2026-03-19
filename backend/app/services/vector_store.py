from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.chunker import ChunkRecord

logger = logging.getLogger(__name__)

VECTOR_SIZE = 768  # nomic-embed-text output dimension


@dataclass
class SearchResult:
    source_filename: str
    page_number: Optional[int]
    section_heading: Optional[str]
    parent_text: str       # context for LLM
    child_text: str        # matched excerpt for citation display
    score: float
    document_id: str


def _get_client():
    from qdrant_client import QdrantClient
    return QdrantClient(url=settings.qdrant_host)


async def initialize_collection() -> None:
    """Create the Qdrant collection if it does not exist."""
    from qdrant_client.models import Distance, SparseVectorParams, VectorParams
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            sparse_vectors_config={
                "sparse": SparseVectorParams(),
            },
        )
        logger.info(f"Created Qdrant collection: {settings.qdrant_collection}")
    else:
        logger.info(f"Qdrant collection '{settings.qdrant_collection}' already exists.")


def delete_points_by_document_id(document_id: str) -> None:
    """Delete all Qdrant points whose payload contains the given document_id."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue
    client = _get_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )
    logger.info(f"Deleted Qdrant vectors for document_id={document_id}")


def clear_collection() -> None:
    """Delete and recreate the Qdrant collection (wipes all vectors)."""
    from qdrant_client.models import Distance, SparseVectorParams, VectorParams
    client = _get_client()
    client.delete_collection(settings.qdrant_collection)
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        sparse_vectors_config={"sparse": SparseVectorParams()},
    )
    logger.info(f"Cleared and recreated collection: {settings.qdrant_collection}")


def collection_exists() -> bool:
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    return settings.qdrant_collection in existing


def index_chunks(chunks: List[ChunkRecord]) -> List[str]:
    """
    Generate embeddings for child texts and upload to Qdrant.
    Returns list of Qdrant point UUIDs.
    """
    from qdrant_client.models import PointStruct

    from app.services.embedder import embedding_service

    if not chunks:
        return []

    BATCH_SIZE = 100
    point_ids: List[str] = []
    client = _get_client()

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        child_texts = [c.child_text for c in batch]

        logger.info(f"Embedding batch {i//BATCH_SIZE + 1}: {len(batch)} chunks")
        embeddings = embedding_service.embed_texts(child_texts)

        points = []
        for chunk, embedding in zip(batch, embeddings):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,  # plain list for unnamed VectorParams
                    payload={
                        "document_id": chunk.document_id,
                        "source_filename": chunk.source_filename,
                        "page_number": chunk.page_number,
                        "section_heading": chunk.section_heading,
                        "chunk_index": chunk.chunk_index,
                        "parent_text": chunk.parent_text,
                        "child_text": chunk.child_text,
                    },
                )
            )

        client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )
        logger.info(f"Indexed {len(points)} points in Qdrant.")

    return point_ids


def search(query: str, top_k: int = 6) -> List[SearchResult]:
    """
    Hybrid search: dense cosine similarity + BM25 sparse search, fused with RRF.
    Returns top_k SearchResult objects with parent text as LLM context.
    """
    from app.services.embedder import embedding_service

    client = _get_client()

    # Dense search
    query_vector = embedding_service.embed_query(query)
    dense_results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k * 2,
        with_payload=True,
    )

    # Sparse BM25 search using rank_bm25 against stored child texts
    sparse_results = _bm25_search(client, query, top_k=top_k * 2)

    # RRF fusion
    fused = _reciprocal_rank_fusion(dense_results, sparse_results, top_k=top_k)
    return fused


def _bm25_search(client, query: str, top_k: int) -> list:
    """Perform BM25 keyword search by scrolling all child texts."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed, skipping sparse search.")
        return []

    # Scroll all points to get child texts (limited to 10k for large collections)
    points, _ = client.scroll(
        collection_name=settings.qdrant_collection,
        limit=10000,
        with_payload=["child_text", "document_id", "source_filename",
                       "page_number", "section_heading", "parent_text", "chunk_index"],
        with_vectors=False,
    )

    if not points:
        return []

    corpus = [p.payload.get("child_text", "") for p in points]
    tokenized = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())

    # Return top_k as mock scored results
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [(points[i], score) for i, score in indexed if score > 0]


def _reciprocal_rank_fusion(
    dense_results: list,
    sparse_results: list,
    top_k: int,
    k: int = 60,
) -> List[SearchResult]:
    """Merge dense and sparse results with RRF scoring."""
    rrf_scores: Dict[str, float] = {}
    payloads: Dict[str, Any] = {}

    # Process dense results (qdrant ScoredPoint objects)
    for rank, hit in enumerate(dense_results):
        pid = str(hit.id)
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
        payloads[pid] = hit.payload

    # Process sparse results (point, score tuples from BM25)
    for rank, (point, _score) in enumerate(sparse_results):
        pid = str(point.id)
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (k + rank + 1)
        payloads[pid] = point.payload

    # Sort by RRF score descending and take top_k
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:top_k]

    results = []
    for pid in sorted_ids:
        payload = payloads[pid]
        results.append(
            SearchResult(
                source_filename=payload.get("source_filename", ""),
                page_number=payload.get("page_number"),
                section_heading=payload.get("section_heading"),
                parent_text=payload.get("parent_text", ""),
                child_text=payload.get("child_text", ""),
                score=rrf_scores[pid],
                document_id=payload.get("document_id", ""),
            )
        )
    return results
