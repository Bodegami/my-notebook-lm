import io
import os
import struct
import zlib
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent.parent / "fixtures"


# ── PDF Extractor ──────────────────────────────────────────────────────────────

class TestPdfExtractor:
    def test_extracts_text_from_sample_pdf(self):
        from app.services.extractors.pdf import PdfExtractor
        extractor = PdfExtractor()
        result = extractor.extract(str(FIXTURES / "sample.pdf"))
        assert len(result.chunks) > 0
        assert any(c.text.strip() for c in result.chunks)

    def test_page_numbers_set_correctly(self):
        from app.services.extractors.pdf import PdfExtractor
        extractor = PdfExtractor()
        result = extractor.extract(str(FIXTURES / "sample.pdf"))
        for chunk in result.chunks:
            assert chunk.page_number is not None
            assert chunk.page_number >= 1

    def test_page_count_set(self):
        from app.services.extractors.pdf import PdfExtractor
        extractor = PdfExtractor()
        result = extractor.extract(str(FIXTURES / "sample.pdf"))
        assert result.page_count is not None
        assert result.page_count >= 1

    def test_scanned_pdf_raises_extraction_error(self):
        from app.services.extractors.base import ExtractionError
        from app.services.extractors.pdf import PdfExtractor
        extractor = PdfExtractor()
        with pytest.raises(ExtractionError, match="scanned"):
            extractor.extract(str(FIXTURES / "scanned_mock.pdf"))

    def test_supports_pdf_extension(self):
        from app.services.extractors.pdf import PdfExtractor
        extractor = PdfExtractor()
        assert extractor.supports(".pdf")
        assert not extractor.supports(".epub")


# ── EPUB Extractor ─────────────────────────────────────────────────────────────

class TestEpubExtractor:
    def test_extracts_text_from_sample_epub(self):
        from app.services.extractors.epub import EpubExtractor
        extractor = EpubExtractor()
        result = extractor.extract(str(FIXTURES / "sample.epub"))
        assert len(result.chunks) > 0
        assert any(c.text.strip() for c in result.chunks)

    def test_section_heading_extracted(self):
        from app.services.extractors.epub import EpubExtractor
        extractor = EpubExtractor()
        result = extractor.extract(str(FIXTURES / "sample.epub"))
        headings = [c.section_heading for c in result.chunks if c.section_heading]
        assert len(headings) > 0

    def test_page_number_is_none(self):
        from app.services.extractors.epub import EpubExtractor
        extractor = EpubExtractor()
        result = extractor.extract(str(FIXTURES / "sample.epub"))
        for chunk in result.chunks:
            assert chunk.page_number is None

    def test_supports_epub_extension(self):
        from app.services.extractors.epub import EpubExtractor
        extractor = EpubExtractor()
        assert extractor.supports(".epub")
        assert not extractor.supports(".pdf")


# ── DOCX Extractor ─────────────────────────────────────────────────────────────

class TestDocxExtractor:
    def test_extracts_text_from_sample_docx(self):
        from app.services.extractors.docx import DocxExtractor
        extractor = DocxExtractor()
        result = extractor.extract(str(FIXTURES / "sample.docx"))
        assert len(result.chunks) > 0
        assert any(c.text.strip() for c in result.chunks)

    def test_section_heading_extracted(self):
        from app.services.extractors.docx import DocxExtractor
        extractor = DocxExtractor()
        result = extractor.extract(str(FIXTURES / "sample.docx"))
        headings = [c.section_heading for c in result.chunks if c.section_heading]
        assert len(headings) > 0

    def test_page_number_is_none(self):
        from app.services.extractors.docx import DocxExtractor
        extractor = DocxExtractor()
        result = extractor.extract(str(FIXTURES / "sample.docx"))
        for chunk in result.chunks:
            assert chunk.page_number is None

    def test_supports_docx_extension(self):
        from app.services.extractors.docx import DocxExtractor
        extractor = DocxExtractor()
        assert extractor.supports(".docx")
        assert extractor.supports(".doc")
        assert not extractor.supports(".pdf")


# ── Markdown Extractor ─────────────────────────────────────────────────────────

class TestMarkdownExtractor:
    def test_extracts_text_from_md(self):
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = MarkdownExtractor()
        result = extractor.extract(str(FIXTURES / "sample.md"))
        assert len(result.chunks) > 0
        assert any(c.text.strip() for c in result.chunks)

    def test_section_headings_from_md(self):
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = MarkdownExtractor()
        result = extractor.extract(str(FIXTURES / "sample.md"))
        headings = [c.section_heading for c in result.chunks if c.section_heading]
        assert len(headings) > 0

    def test_txt_no_section_heading(self):
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = MarkdownExtractor()
        result = extractor.extract(str(FIXTURES / "sample.txt"))
        for chunk in result.chunks:
            assert chunk.section_heading is None
            assert chunk.page_number is None

    def test_supports_md_and_txt(self):
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = MarkdownExtractor()
        assert extractor.supports(".md")
        assert extractor.supports(".txt")
        assert not extractor.supports(".pdf")


# ── Factory ────────────────────────────────────────────────────────────────────

class TestExtractorFactory:
    def test_returns_pdf_extractor(self):
        from app.services.extractors.factory import ExtractorFactory
        from app.services.extractors.pdf import PdfExtractor
        extractor = ExtractorFactory.get_extractor("book.pdf")
        assert isinstance(extractor, PdfExtractor)

    def test_returns_epub_extractor(self):
        from app.services.extractors.factory import ExtractorFactory
        from app.services.extractors.epub import EpubExtractor
        extractor = ExtractorFactory.get_extractor("book.epub")
        assert isinstance(extractor, EpubExtractor)

    def test_returns_docx_extractor(self):
        from app.services.extractors.factory import ExtractorFactory
        from app.services.extractors.docx import DocxExtractor
        extractor = ExtractorFactory.get_extractor("report.docx")
        assert isinstance(extractor, DocxExtractor)

    def test_returns_markdown_extractor_for_md(self):
        from app.services.extractors.factory import ExtractorFactory
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = ExtractorFactory.get_extractor("notes.md")
        assert isinstance(extractor, MarkdownExtractor)

    def test_returns_markdown_extractor_for_txt(self):
        from app.services.extractors.factory import ExtractorFactory
        from app.services.extractors.markdown import MarkdownExtractor
        extractor = ExtractorFactory.get_extractor("data.txt")
        assert isinstance(extractor, MarkdownExtractor)

    def test_unsupported_format_raises(self):
        from app.services.extractors.base import UnsupportedFormatError
        from app.services.extractors.factory import ExtractorFactory
        with pytest.raises(UnsupportedFormatError):
            ExtractorFactory.get_extractor("data.xlsx")
