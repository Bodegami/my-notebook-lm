"""
Integration tests for the document ingestion pipeline.
Requires running Docker services: backend + qdrant.

Run with:
    pytest tests/backend/integration/test_ingestion_pipeline.py -v --timeout=60
"""
import asyncio
import time
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://localhost:8000"
FIXTURES = Path(__file__).parent.parent.parent / "fixtures"
TIMEOUT = 60  # seconds to wait for indexing


@pytest.mark.integration
class TestIngestionPipeline:
    def test_upload_pdf_reaches_indexed_status(self):
        """Upload sample.pdf and poll until status=indexed."""
        sample = FIXTURES / "sample.pdf"
        assert sample.exists(), "sample.pdf fixture not found"

        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            # Upload
            with open(sample, "rb") as f:
                resp = client.post("/api/documents/upload", files={"files": ("sample.pdf", f, "application/pdf")})
            assert resp.status_code == 202, f"Upload failed: {resp.text}"
            data = resp.json()
            assert len(data) == 1
            doc_id = data[0]["document_id"]
            assert data[0]["status"] == "pending"

            # Poll until indexed or timeout
            deadline = time.time() + TIMEOUT
            while time.time() < deadline:
                status_resp = client.get(f"/api/documents/{doc_id}")
                assert status_resp.status_code == 200
                doc = status_resp.json()
                if doc["status"] == "indexed":
                    break
                if doc["status"] == "error":
                    pytest.fail(f"Ingestion failed: {doc['error_message']}")
                time.sleep(1)
            else:
                pytest.fail(f"Document did not reach indexed status within {TIMEOUT}s")

            # Verify chunk_count > 0
            assert doc["chunk_count"] is not None and doc["chunk_count"] > 0

            # Verify it appears in the document list
            list_resp = client.get("/api/documents")
            assert list_resp.status_code == 200
            ids = [d["id"] for d in list_resp.json()["documents"]]
            assert doc_id in ids

            return doc_id

    def test_document_appears_in_list(self):
        """GET /api/documents returns at least one document after upload."""
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            resp = client.get("/api/documents")
            assert resp.status_code == 200
            body = resp.json()
            assert "documents" in body

    def test_delete_document_removes_from_list(self):
        """Upload a document then delete it; verify it is gone."""
        sample = FIXTURES / "sample.md"
        assert sample.exists()

        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            # Upload
            with open(sample, "rb") as f:
                resp = client.post("/api/documents/upload", files={"files": ("sample.md", f, "text/markdown")})
            assert resp.status_code == 202
            doc_id = resp.json()[0]["document_id"]

            # Poll until terminal
            deadline = time.time() + TIMEOUT
            while time.time() < deadline:
                doc = client.get(f"/api/documents/{doc_id}").json()
                if doc["status"] in ("indexed", "error"):
                    break
                time.sleep(1)

            # Delete
            del_resp = client.delete(f"/api/documents/{doc_id}")
            assert del_resp.status_code == 204

            # Verify gone
            get_resp = client.get(f"/api/documents/{doc_id}")
            assert get_resp.status_code == 404

    def test_clear_all_empties_knowledge_base(self):
        """DELETE /api/documents clears all documents."""
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            resp = client.delete("/api/documents")
            assert resp.status_code == 204

            list_resp = client.get("/api/documents")
            assert list_resp.status_code == 200
            assert list_resp.json()["documents"] == []

    def test_unsupported_format_returns_422(self):
        """Uploading an unsupported file format returns HTTP 422."""
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            fake_content = b"not a real file"
            resp = client.post(
                "/api/documents/upload",
                files={"files": ("data.xlsx", fake_content, "application/vnd.ms-excel")},
            )
            assert resp.status_code == 422
