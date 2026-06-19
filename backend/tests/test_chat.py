import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

def test_chat_message_endpoint_no_rag(client: TestClient):
    payload = {
        "session_id": "session-123",
        "message": "Hello AI assistant!",
        "use_rag": False
    }
    
    # Mock LLM service streaming response
    async def mock_generator(*args, **kwargs):
        yield "Hello"
        yield "!"
        
    with patch("app.llm.ollama.llm_service.generate_stream", side_effect=mock_generator):
        response = client.post("/api/v1/chat/message", json=payload)
        
    assert response.status_code == 200
    assert response.text == "Hello!"

def test_chat_message_endpoint_with_rag(client: TestClient):
    payload = {
        "session_id": "session-123",
        "message": "What is the result?",
        "use_rag": True
    }
    
    # Mock FAISS query returning 1 matching chunk
    mock_chunks = [
        {
            "document_id": "doc-uuid",
            "filename": "result.pdf",
            "text": "The project result is positive.",
            "chunk_index": 0,
            "score": 0.12
        }
    ]
    
    # Mock LLM streamer
    async def mock_generator(prompt, *args, **kwargs):
        # Verify that prompt contains the retrieved context
        assert "The project result is positive" in prompt
        assert "result.pdf" in prompt
        yield "The"
        yield " result"
        yield " is"
        yield " positive."
        
    with patch("app.vectorstore.faiss.vector_store_service.similarity_search", return_value=mock_chunks), \
         patch("app.llm.ollama.llm_service.generate_stream", side_effect=mock_generator) as mock_gen_method:
         
        response = client.post("/api/v1/chat/message", json=payload)
        
    assert response.status_code == 200
    assert response.text == "The result is positive."
