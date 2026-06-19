from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: datetime = datetime.now()

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    use_rag: bool = True
