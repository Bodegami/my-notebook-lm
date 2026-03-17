from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ExtractionError(Exception):
    """Raised when a document cannot be extracted (e.g., scanned PDF, corrupt file)."""


class UnsupportedFormatError(Exception):
    """Raised when the file format is not supported by any extractor."""


@dataclass
class ExtractedChunk:
    text: str
    page_number: Optional[int]
    section_heading: Optional[str]
    chunk_index: int


@dataclass
class ExtractionResult:
    chunks: List[ExtractedChunk]
    page_count: Optional[int]
    metadata: Dict = field(default_factory=dict)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult:
        ...

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        ...
