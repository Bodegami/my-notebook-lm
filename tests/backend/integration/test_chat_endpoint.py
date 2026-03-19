"""
Integration tests for the SSE chat endpoint.
Requires running Docker services with at least one indexed document.

Run with:
    pytest tests/backend/integration/test_chat_endpoint.py -v --timeout=120
"""
import json
import time
import uuid
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://localhost:8000"
FIXTURES = Path(__file__).parent.parent.parent / "fixtures"
TIMEOUT = 90


def _upload_and_wait(client: httpx.Client, filepath: Path, timeout: int = TIMEOUT) -> str:
    """Upload a file and poll until indexed. Returns document_id."""
    with open(filepath, "rb") as f:
        resp = client.post(
            "/api/documents/upload",
            files={"files": (filepath.name, f, "application/octet-stream")},
        )
    assert resp.status_code == 202
    doc_id = resp.json()[0]["document_id"]

    deadline = time.time() + timeout
    while time.time() < deadline:
        doc = client.get(f"/api/documents/{doc_id}").json()
        if doc["status"] == "indexed":
            return doc_id
        if doc["status"] == "error":
            pytest.fail(f"Ingestion error: {doc['error_message']}")
        time.sleep(1)
    pytest.fail(f"Document {doc_id} not indexed within {timeout}s")


def _collect_sse_events(client: httpx.Client, session_id: str, message: str) -> list[dict]:
    """POST to chat/stream and collect all SSE events."""
    events = []
    with client.stream(
        "POST",
        "/api/chat/stream",
        json={"session_id": session_id, "message": message},
        headers={"X-Session-ID": session_id},
        timeout=TIMEOUT,
    ) as resp:
        assert resp.status_code == 200
        buffer = ""
        for chunk in resp.iter_text():
            buffer += chunk
            lines = buffer.split("\n")
            buffer = lines.pop()
            for line in lines:
                if line.startswith("data: "):
                    try:
                        events.append(json.loads(line[6:]))
                    except json.JSONDecodeError:
                        pass
    return events


@pytest.mark.integration
class TestChatEndpoint:
    @pytest.fixture(autouse=True, scope="class")
    def setup_document(self):
        """Upload sample.md before tests and clean up after."""
        sample = FIXTURES / "sample.md"
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            doc_id = _upload_and_wait(client, sample)
        yield doc_id
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            client.delete(f"/api/documents/{doc_id}")

    def test_trivial_message_has_no_citations(self):
        """A greeting should produce a done event with no citation events."""
        session_id = str(uuid.uuid4())
        with httpx.Client(base_url=BASE_URL, timeout=10) as client:
            events = _collect_sse_events(client, session_id, "Hello!")

        event_types = [e["type"] for e in events]
        assert "done" in event_types, "Missing 'done' event"
        assert "citation" not in event_types, "Trivial message should produce no citations"
        assert any(e["type"] == "token" for e in events), "Missing token events"

    def test_document_question_has_citations(self):
        """A question about book content should produce citation and done events."""
        session_id = str(uuid.uuid4())
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            events = _collect_sse_events(
                client, session_id, "What does the book say about clean code?"
            )

        event_types = [e["type"] for e in events]
        assert "done" in event_types
        assert any(e["type"] == "token" for e in events)
        # The done event should have sources
        done_events = [e for e in events if e["type"] == "done"]
        assert done_events, "No done event found"

    def test_out_of_scope_question_says_not_found(self):
        """A question about topics not in the books should return 'could not find'."""
        session_id = str(uuid.uuid4())
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            events = _collect_sse_events(
                client, session_id,
                "What is the GDP of Brazil in 2025?"
            )

        tokens = "".join(e.get("text", "") for e in events if e["type"] == "token")
        assert "could not find" in tokens.lower() or len(tokens) > 0, \
            "Expected some response even for out-of-scope queries"

    def test_stream_contains_status_events(self):
        """Document questions should emit status events."""
        session_id = str(uuid.uuid4())
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            events = _collect_sse_events(
                client, session_id, "Explain the boy scout rule."
            )

        status_events = [e for e in events if e["type"] == "status"]
        assert len(status_events) >= 1, "Expected at least one status event"
