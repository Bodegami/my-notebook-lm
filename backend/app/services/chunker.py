from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.extractors.base import ExtractionResult

# Approximate chars-per-token ratio for English text
CHARS_PER_TOKEN = 4


@dataclass
class ChunkRecord:
    child_text: str        # text to embed and search
    parent_text: str       # text to send to LLM as context
    source_filename: str
    page_number: Optional[int]
    section_heading: Optional[str]
    chunk_index: int
    document_id: str


def chunk_document(
    extraction_result: ExtractionResult,
    document_id: str,
    filename: str,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
    parent_chunk_size: int = 1000,
) -> List[ChunkRecord]:
    """
    Apply the Parent Document strategy:
    - Each extracted section/page block becomes one or more parent chunks (~parent_chunk_size tokens).
    - Each parent chunk is split into smaller child chunks (~chunk_size tokens).
    - Child chunks reference the parent text for LLM context.
    """
    if not extraction_result.chunks:
        return []

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size * CHARS_PER_TOKEN,
        chunk_overlap=chunk_overlap * CHARS_PER_TOKEN,
        length_function=len,
    )
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size * CHARS_PER_TOKEN,
        chunk_overlap=0,
        length_function=len,
    )

    records: List[ChunkRecord] = []

    for extracted_chunk in extraction_result.chunks:
        text = extracted_chunk.text
        if not text.strip():
            continue

        # Split into parent chunks
        parent_texts = parent_splitter.split_text(text)

        for parent_text in parent_texts:
            if not parent_text.strip():
                continue

            # Split parent into child chunks
            child_texts = child_splitter.split_text(parent_text)

            for child_text in child_texts:
                if not child_text.strip():
                    continue

                records.append(
                    ChunkRecord(
                        child_text=child_text,
                        parent_text=parent_text,
                        source_filename=filename,
                        page_number=extracted_chunk.page_number,
                        section_heading=extracted_chunk.section_heading,
                        chunk_index=len(records),
                        document_id=document_id,
                    )
                )

    return records
