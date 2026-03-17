import re
from pathlib import Path
from typing import List, Optional

from app.services.extractors.base import BaseExtractor, ExtractionResult, ExtractedChunk

HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
TXT_BLOCK_SIZE = 2000  # characters per block for plain text


class MarkdownExtractor(BaseExtractor):
    def extract(self, file_path: str) -> ExtractionResult:
        ext = Path(file_path).suffix.lower()
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")

        if ext == ".md":
            return self._extract_markdown(text)
        return self._extract_txt(text)

    def _extract_markdown(self, text: str) -> ExtractionResult:
        chunks: List[ExtractedChunk] = []
        current_heading: Optional[str] = None
        current_lines: List[str] = []

        def flush():
            content = "\n".join(current_lines).strip()
            if content:
                chunks.append(
                    ExtractedChunk(
                        text=content,
                        page_number=None,
                        section_heading=current_heading,
                        chunk_index=len(chunks),
                    )
                )

        for line in text.splitlines():
            m = HEADING_RE.match(line)
            if m:
                flush()
                current_lines = []
                current_heading = m.group(2).strip()
            else:
                current_lines.append(line)

        flush()
        return ExtractionResult(chunks=chunks, page_count=None)

    def _extract_txt(self, text: str) -> ExtractionResult:
        chunks: List[ExtractedChunk] = []
        for i in range(0, len(text), TXT_BLOCK_SIZE):
            block = text[i : i + TXT_BLOCK_SIZE].strip()
            if block:
                chunks.append(
                    ExtractedChunk(
                        text=block,
                        page_number=None,
                        section_heading=None,
                        chunk_index=len(chunks),
                    )
                )
        return ExtractionResult(chunks=chunks, page_count=None)

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() in {".md", ".txt"}
