from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas import ChatMessageRequest, ChatSessionCreate, ChatSessionResponse
from app.vectorstore import vector_store_service
from app.llm import llm_service
from typing import List

router = APIRouter()

@router.post("/session", response_model=ChatSessionResponse)
async def create_chat_session(payload: ChatSessionCreate):
    """
    Creates a new chat session/conversation thread.
    """
    # TODO: Implement chat session metadata persistence
    return {"id": "session-123", "title": payload.title or "New Chat", "messages": []}

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions():
    """
    Lists all stored local chat sessions.
    """
    # TODO: Retrieve list of saved chat sessions from SQLite/metadata JSON
    return []

@router.post("/message")
async def send_message(payload: ChatMessageRequest):
    """
    Retrieves semantic document context (RAG) if requested,
    formulates the context-aware prompt, and streams response tokens from Ollama.
    """
    context_block = ""
    
    # 1. FAISS Search if RAG is toggled
    if payload.use_rag:
        try:
            # Query top 3 matching chunks
            retrieved_chunks = vector_store_service.similarity_search(payload.message, k=3)
            
            if retrieved_chunks:
                context_parts = []
                for chunk in retrieved_chunks:
                    context_parts.append(
                        f"[File: {chunk.get('filename')} | Chunk: {chunk.get('chunk_index')}]:\n"
                        f"{chunk.get('text')}"
                    )
                context_block = "\n\n".join(context_parts)
        except Exception as e:
            # Fallback gracefully or log but continue query without context
            pass
            
    # 2. Build Context-Aware Prompt
    if context_block:
        prompt = (
            "You are Lexora, a helpful offline AI document assistant.\n"
            "Answer the user's question using the retrieved context pieces below.\n"
            "If the context does not contain the answer, reply stating you don't know "
            "based on the documents. Keep responses accurate, clear and derived directly from context.\n\n"
            "=== Retextual Context ===\n"
            f"{context_block}\n"
            "=========================\n\n"
            f"Question: {payload.message}\n"
            "Answer:"
        )
    else:
        # Default prompt if RAG is disabled or vector store is empty
        prompt = (
            "You are Lexora, a helpful offline AI document assistant.\n\n"
            f"Question: {payload.message}\n"
            "Answer:"
        )

    # 3. Stream Response
    async def response_streamer():
        async for chunk in llm_service.generate_stream(prompt):
            yield chunk

    return StreamingResponse(response_streamer(), media_type="text/plain")
