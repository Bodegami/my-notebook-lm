from datetime import datetime

import pytest

from app.schemas.chat import ChatRequest, Citation, SSEEvent
from app.schemas.document import DocumentListResponse, DocumentResponse, UploadResponse


class TestDocumentResponse:
    def test_serializes_from_dict(self):
        data = {
            "id": "abc-123",
            "filename": "test.pdf",
            "file_format": "pdf",
            "upload_time": datetime(2026, 1, 1, 12, 0, 0),
            "status": "indexed",
            "error_message": None,
            "page_count": 42,
            "chunk_count": 100,
        }
        doc = DocumentResponse(**data)
        assert doc.id == "abc-123"
        assert doc.filename == "test.pdf"
        assert doc.page_count == 42
        assert doc.error_message is None

    def test_optional_fields_default_none(self):
        data = {
            "id": "xyz",
            "filename": "notes.md",
            "file_format": "md",
            "upload_time": datetime.utcnow(),
            "status": "pending",
        }
        doc = DocumentResponse(**data)
        assert doc.error_message is None
        assert doc.page_count is None
        assert doc.chunk_count is None


class TestDocumentListResponse:
    def test_empty_list(self):
        resp = DocumentListResponse(documents=[])
        assert resp.documents == []


class TestUploadResponse:
    def test_basic_fields(self):
        resp = UploadResponse(document_id="123", filename="book.pdf", status="pending")
        assert resp.document_id == "123"
        assert resp.status == "pending"


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(session_id="sess-1", message="Hello")
        assert req.session_id == "sess-1"
        assert req.message == "Hello"

    def test_missing_session_id_raises(self):
        with pytest.raises(Exception):
            ChatRequest(message="Hello")

    def test_missing_message_raises(self):
        with pytest.raises(Exception):
            ChatRequest(session_id="sess-1")


class TestCitation:
    def test_with_page_number(self):
        c = Citation(id=1, source_filename="book.pdf", page_number=42, excerpt="Some text")
        assert c.page_number == 42
        assert c.section_heading is None

    def test_with_section_heading_only(self):
        c = Citation(id=2, source_filename="notes.md", section_heading="Introduction", excerpt="...")
        assert c.page_number is None
        assert c.section_heading == "Introduction"

    def test_both_null_is_valid(self):
        c = Citation(id=3, source_filename="doc.txt", excerpt="text")
        assert c.page_number is None
        assert c.section_heading is None


class TestSSEEvent:
    def test_status_event(self):
        ev = SSEEvent(type="status", text="Searching...")
        assert ev.type == "status"
        assert ev.text == "Searching..."
        assert ev.citation is None

    def test_done_event_with_sources(self):
        sources = [Citation(id=1, source_filename="a.pdf", excerpt="text")]
        ev = SSEEvent(type="done", sources=sources)
        assert ev.type == "done"
        assert len(ev.sources) == 1
