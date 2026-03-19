from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models.document import Document
from app.schemas.document import DocumentListResponse, DocumentResponse, UploadResponse
from app.services import vector_store

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".epub", ".docx", ".doc", ".md", ".txt"}


def _doc_to_response(doc: Document) -> DocumentResponse:
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_format=doc.file_format,
        upload_time=doc.upload_time,
        status=doc.status,
        error_message=doc.error_message,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
    )


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/documents/upload", response_model=List[UploadResponse], status_code=202)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session: Session = Depends(get_session),
):
    responses = []
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()

        # Validate extension
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        # Validate size (read content first)
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File '{filename}' exceeds maximum size of {settings.max_upload_size_mb} MB.",
            )

        document_id = str(uuid.uuid4())
        saved_path = upload_dir / f"{document_id}_{filename}"
        saved_path.write_bytes(content)

        # Create SQLite record
        doc = Document(
            id=document_id,
            filename=filename,
            file_format=ext.lstrip("."),
            status="pending",
        )
        session.add(doc)
        session.commit()

        # Schedule background ingestion
        from app.services.ingestion import ingest_document
        from app.database import engine
        from sqlmodel import Session as DBSession

        def make_ingest_task(path, did, fname):
            async def _task():
                with DBSession(engine) as bg_session:
                    await ingest_document(str(path), did, fname, bg_session)
            return _task

        background_tasks.add_task(make_ingest_task(saved_path, document_id, filename))

        responses.append(UploadResponse(
            document_id=document_id,
            filename=filename,
            status="pending",
        ))

    return responses


# ── List & Status ──────────────────────────────────────────────────────────────

@router.get("/documents", response_model=DocumentListResponse)
def list_documents(session: Session = Depends(get_session)):
    docs = session.exec(select(Document).order_by(Document.upload_time.desc())).all()
    return DocumentListResponse(documents=[_doc_to_response(d) for d in docs])


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, session: Session = Depends(get_session)):
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _doc_to_response(doc)


# ── Delete Single ──────────────────────────────────────────────────────────────

@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, session: Session = Depends(get_session)):
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove Qdrant vectors
    vector_store.delete_points_by_document_id(document_id)

    # Remove uploaded file
    upload_dir = Path(settings.upload_dir)
    for f in upload_dir.glob(f"{document_id}_*"):
        try:
            f.unlink()
        except Exception:
            pass

    session.delete(doc)
    session.commit()


# ── Clear All ──────────────────────────────────────────────────────────────────

@router.delete("/documents", status_code=204)
def clear_all_documents(session: Session = Depends(get_session)):
    # Clear Qdrant collection
    vector_store.clear_collection()

    # Delete all uploaded files
    upload_dir = Path(settings.upload_dir)
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            try:
                f.unlink()
            except Exception:
                pass

    # Delete all SQLite records
    docs = session.exec(select(Document)).all()
    for doc in docs:
        session.delete(doc)
    session.commit()
