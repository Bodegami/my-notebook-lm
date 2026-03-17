import subprocess
from pathlib import Path
from typing import List, Optional

from app.services.extractors.base import (
    BaseExtractor,
    ExtractionError,
    ExtractionResult,
    ExtractedChunk,
)

HEADING_STYLES = {"Heading 1", "Heading 2", "Heading 3"}


class DocxExtractor(BaseExtractor):
    def extract(self, file_path: str) -> ExtractionResult:
        ext = Path(file_path).suffix.lower()
        if ext == ".doc":
            return self._extract_doc(file_path)
        return self._extract_docx(file_path)

    def _extract_docx(self, file_path: str) -> ExtractionResult:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("python-docx is required.")

        doc = Document(file_path)
        chunks: List[ExtractedChunk] = []
        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []

        def flush():
            if current_paragraphs:
                text = "\n".join(current_paragraphs)
                chunks.append(
                    ExtractedChunk(
                        text=text,
                        page_number=None,
                        section_heading=current_heading,
                        chunk_index=len(chunks),
                    )
                )

        for para in doc.paragraphs:
            if para.style is not None and para.style.name in HEADING_STYLES:
                flush()
                current_paragraphs = []
                current_heading = para.text.strip() or current_heading
            elif para.text.strip():
                current_paragraphs.append(para.text.strip())

        flush()
        return ExtractionResult(chunks=chunks, page_count=None)

    def _extract_doc(self, file_path: str) -> ExtractionResult:
        try:
            result = subprocess.run(
                ["antiword", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise ExtractionError(f"antiword failed: {result.stderr}")
            text = result.stdout
        except FileNotFoundError:
            raise ExtractionError(
                "Legacy .doc files require antiword. Please convert to .docx."
            )

        chunks = [
            ExtractedChunk(
                text=text,
                page_number=None,
                section_heading=None,
                chunk_index=0,
            )
        ]
        return ExtractionResult(chunks=chunks, page_count=None)

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() in {".docx", ".doc"}
