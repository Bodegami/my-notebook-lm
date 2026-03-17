from app.services.extractors.base import (
    BaseExtractor,
    ExtractionError,
    ExtractionResult,
    ExtractedChunk,
)


class PdfExtractor(BaseExtractor):
    SCANNED_CHAR_THRESHOLD = 50  # pages with fewer chars are likely scanned

    def extract(self, file_path: str) -> ExtractionResult:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ExtractionError("pypdf is not installed.")

        reader = PdfReader(file_path)
        page_count = len(reader.pages)

        chunks: list[ExtractedChunk] = []
        empty_pages = 0

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if len(text.strip()) < self.SCANNED_CHAR_THRESHOLD:
                empty_pages += 1
                continue
            chunks.append(
                ExtractedChunk(
                    text=text,
                    page_number=i + 1,
                    section_heading=None,
                    chunk_index=len(chunks),
                )
            )

        if not chunks:
            raise ExtractionError(
                "PDF appears to be scanned (no extractable text found). "
                "OCR is not supported in v1."
            )

        return ExtractionResult(chunks=chunks, page_count=page_count)

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".pdf"
