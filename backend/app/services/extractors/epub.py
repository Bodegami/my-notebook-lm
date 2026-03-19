from typing import Optional

from app.services.extractors.base import BaseExtractor, ExtractionResult, ExtractedChunk


class EpubExtractor(BaseExtractor):
    def extract(self, file_path: str) -> ExtractionResult:
        try:
            import ebooklib
            from bs4 import BeautifulSoup
            from ebooklib import epub
        except ImportError:
            raise ImportError("ebooklib and beautifulsoup4 are required.")

        book = epub.read_epub(file_path)
        chunks: list[ExtractedChunk] = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "html.parser")

            # Extract section heading from title attribute or first heading tag
            heading: Optional[str] = None
            if item.get_name():
                heading = item.get_name()
            for tag in ("h1", "h2", "h3"):
                h = soup.find(tag)
                if h and h.get_text(strip=True):
                    heading = h.get_text(strip=True)
                    break

            text = soup.get_text(separator="\n", strip=True)
            if not text.strip():
                continue

            chunks.append(
                ExtractedChunk(
                    text=text,
                    page_number=None,
                    section_heading=heading,
                    chunk_index=len(chunks),
                )
            )

        return ExtractionResult(chunks=chunks, page_count=None)

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".epub"
