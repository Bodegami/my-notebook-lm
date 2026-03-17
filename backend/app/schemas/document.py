from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_format: str
    upload_time: datetime
    status: str
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
