from typing import List, Literal, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class Citation(BaseModel):
    id: int
    source_filename: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    excerpt: str


class SSEEvent(BaseModel):
    type: Literal["status", "token", "citation", "done", "error"]
    text: Optional[str] = None
    citation: Optional[Citation] = None
    sources: Optional[List[Citation]] = None
