from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

from sqlmodel import Session

from app.config import settings
from app.models.document import Document
from app.services.chunker import chunk_document
from app.services.extractors.factory import ExtractorFactory
from app.services.vector_store import index_chunks

logger = logging.getLogger(__name__)


def _update_status(
    session: Session,
    document_id: str,
    status: str,
    error_message: Optional[str] = None,
    page_count: Optional[int] = None,
    chunk_count: Optional[int] = None,
    qdrant_ids: Optional[list] = None,
) -> None:
    doc = session.get(Document, document_id)
    if doc is None:
        logger.warning(f"Document {document_id} not found when updating status.")
        return
    doc.status = status
    if error_message is not None:
        doc.error_message = error_message
    if page_count is not None:
        doc.page_count = page_count
    if chunk_count is not None:
        doc.chunk_count = chunk_count
    if qdrant_ids is not None:
        doc.qdrant_ids = json.dumps(qdrant_ids)
    session.add(doc)
    session.commit()


async def ingest_document(
    file_path: str,
    document_id: str,
    filename: str,
    db_session: Session,
) -> None:
    """
    Full async ingestion pipeline:
    1. extract  → raw text + metadata from file
    2. chunk    → parent/child ChunkRecord list
    3. embed    → generate dense vectors (inside index_chunks)
    4. index    → upload to Qdrant, store point IDs
    """
    try:
        # Step 1: Extract (CPU-bound — run in thread)
        _update_status(db_session, document_id, "extracting")
        extractor = ExtractorFactory.get_extractor(filename)
        extraction_result = await asyncio.to_thread(extractor.extract, file_path)
        logger.info(f"Extracted {len(extraction_result.chunks)} sections from {filename}")

        # Step 2: Chunk (CPU-bound — run in thread)
        _update_status(db_session, document_id, "chunking")
        chunks = await asyncio.to_thread(
            chunk_document,
            extraction_result,
            document_id=document_id,
            filename=filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            parent_chunk_size=settings.parent_chunk_size,
        )
        logger.info(f"Created {len(chunks)} chunks for {filename}")

        # Step 3 & 4: Embed + Index (CPU-bound — run in thread)
        _update_status(db_session, document_id, "embedding")
        point_ids = await asyncio.to_thread(index_chunks, chunks)
        logger.info(f"Indexed {len(point_ids)} points in Qdrant for {filename}")

        # Mark as indexed
        _update_status(
            db_session,
            document_id,
            "indexed",
            page_count=extraction_result.page_count,
            chunk_count=len(chunks),
            qdrant_ids=point_ids,
        )
        logger.info(f"Document {filename} fully indexed.")

    except Exception as exc:
        logger.error(f"Ingestion failed for {filename}: {exc}", exc_info=True)
        _update_status(db_session, document_id, "error", error_message=str(exc))
        # Clean up uploaded file on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
