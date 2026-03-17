from app.services.extractors.base import ExtractionResult, ExtractedChunk
from app.services.chunker import ChunkRecord, chunk_document


def make_extraction_result(num_pages: int = 3, chars_per_page: int = 2000) -> ExtractionResult:
    """Create a mock ExtractionResult with text spread across multiple pages."""
    chunks = []
    for i in range(num_pages):
        text = f"Page {i+1} content: " + ("Lorem ipsum dolor sit amet. " * (chars_per_page // 30))
        chunks.append(
            ExtractedChunk(
                text=text,
                page_number=i + 1,
                section_heading=f"Section {i+1}" if i % 2 == 0 else None,
                chunk_index=i,
            )
        )
    return ExtractionResult(chunks=chunks, page_count=num_pages)


class TestChunkDocument:
    def test_returns_chunk_records(self):
        result = make_extraction_result(num_pages=1)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        assert len(records) > 0
        assert all(isinstance(r, ChunkRecord) for r in records)

    def test_child_chunks_within_size_bounds(self):
        """Child chunks should be <= chunk_size + chunk_overlap tokens (words as proxy)."""
        result = make_extraction_result(num_pages=3, chars_per_page=5000)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf",
                                  chunk_size=300, chunk_overlap=50, parent_chunk_size=1000)
        for record in records:
            # Approximate token count as word count (rough proxy)
            word_count = len(record.child_text.split())
            assert word_count <= 400, f"Child chunk too large: {word_count} words"

    def test_each_child_has_parent_text(self):
        result = make_extraction_result(num_pages=2)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        for record in records:
            assert record.parent_text, "Every child chunk must have a non-empty parent_text"
            assert len(record.parent_text) >= len(record.child_text) or len(record.parent_text) > 0

    def test_metadata_propagated(self):
        result = make_extraction_result(num_pages=3)
        records = chunk_document(result, document_id="doc-xyz", filename="book.pdf")
        for record in records:
            assert record.document_id == "doc-xyz"
            assert record.source_filename == "book.pdf"

    def test_page_number_propagated(self):
        result = make_extraction_result(num_pages=3)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        page_numbers = {r.page_number for r in records if r.page_number is not None}
        assert len(page_numbers) >= 1, "At least one chunk should have a page number"

    def test_section_heading_propagated(self):
        result = make_extraction_result(num_pages=3)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        # Sections 1 and 3 (index 0 and 2) have headings in our fixture
        headings = {r.section_heading for r in records if r.section_heading is not None}
        assert len(headings) >= 1, "At least one chunk should have a section heading"

    def test_chunk_index_assigned(self):
        result = make_extraction_result(num_pages=2)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        indices = [r.chunk_index for r in records]
        assert indices == list(range(len(records))), "chunk_index should be sequential from 0"

    def test_no_text_lost(self):
        """All source text characters should be accounted for across parent chunks."""
        result = make_extraction_result(num_pages=2, chars_per_page=1000)
        total_source_chars = sum(len(c.text) for c in result.chunks)
        records = chunk_document(result, document_id="doc-1", filename="test.pdf")
        # Collect unique parent texts (deduplicated by content)
        all_parent_text = " ".join(set(r.parent_text for r in records))
        # Parent chunks should cover all the source text (allowing for overlap)
        assert len(all_parent_text) >= total_source_chars * 0.9, "Too much text was lost"

    def test_empty_extraction_result(self):
        empty = ExtractionResult(chunks=[], page_count=0)
        records = chunk_document(empty, document_id="doc-1", filename="empty.pdf")
        assert records == []
