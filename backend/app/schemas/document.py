from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str  # "processing", "completed", "failed"
    chunk_count: Optional[int] = 0
    file_size_bytes: Optional[int] = 0
    uploaded_at: datetime = datetime.now()
    error_message: Optional[str] = None

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
