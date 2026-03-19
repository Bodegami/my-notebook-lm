from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: str = Field(primary_key=True)
    filename: str
    file_format: str  # pdf | epub | docx | doc | md | txt
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")  # pending | extracting | chunking | embedding | indexed | error
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    qdrant_ids: Optional[str] = None  # JSON array of Qdrant point UUIDs
