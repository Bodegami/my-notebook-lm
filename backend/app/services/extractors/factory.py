from pathlib import Path

from app.services.extractors.base import BaseExtractor, UnsupportedFormatError

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".docx", ".doc", ".md", ".txt"}


class ExtractorFactory:
    @staticmethod
    def get_extractor(filename: str) -> BaseExtractor:
        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            from app.services.extractors.pdf import PdfExtractor
            return PdfExtractor()
        elif ext == ".epub":
            from app.services.extractors.epub import EpubExtractor
            return EpubExtractor()
        elif ext in {".docx", ".doc"}:
            from app.services.extractors.docx import DocxExtractor
            return DocxExtractor()
        elif ext in {".md", ".txt"}:
            from app.services.extractors.markdown import MarkdownExtractor
            return MarkdownExtractor()
        else:
            raise UnsupportedFormatError(
                f"Unsupported file format: '{ext}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
