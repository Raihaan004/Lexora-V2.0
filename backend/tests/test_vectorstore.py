import pytest
import numpy as np
import os
from unittest.mock import MagicMock, patch
from app.vectorstore.faiss import FAISSService
from app.core.config import settings

def clean_test_indices():
    """Removes test index and metadata files generated during test runs."""
    idx_path = settings.FAISS_DIR / "test_index.faiss"
    meta_path = settings.METADATA_DIR / "test_vector_chunks.json"
    if idx_path.exists():
        os.remove(idx_path)
    if meta_path.exists():
        os.remove(meta_path)

@pytest.fixture
def temp_faiss_service():
    clean_test_indices()
    # Instantiate FAISSService and point to test paths
    service = FAISSService()
    service.index_path = settings.FAISS_DIR / "test_index.faiss"
    service.metadata_path = settings.METADATA_DIR / "test_vector_chunks.json"
    service._load_store()
    yield service
    clean_test_indices()

@patch("app.embeddings.bge.SentenceTransformer")
def test_vectorstore_lifecycle(mock_sentence_transformer, temp_faiss_service):
    service = temp_faiss_service
    assert service.index.ntotal == 0
    assert len(service.metadata) == 0
    
    # 1. Prepare dummy data
    chunks = [
        {"document_id": "doc-A", "filename": "a.txt", "text": "This is chunk A", "chunk_index": 0},
        {"document_id": "doc-A", "filename": "a.txt", "text": "This is chunk B", "chunk_index": 1},
        {"document_id": "doc-B", "filename": "b.txt", "text": "This is chunk C", "chunk_index": 0}
    ]
    # Simulate BGE embeddings for these 3 chunks (dimension 384)
    embeddings = np.random.rand(3, 384).astype(np.float32)
    # Normalize them
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    # 2. Add documents to FAISS
    service.add_documents(chunks, embeddings)
    assert service.index.ntotal == 3
    assert len(service.metadata) == 3
    
    # Verify metadata registry indices mapped correctly
    assert service.metadata["0"]["document_id"] == "doc-A"
    assert service.metadata["2"]["document_id"] == "doc-B"
    
    # Verify files saved on disk
    assert service.index_path.exists()
    assert service.metadata_path.exists()

    # 3. Simulate similarity search with mocked embedding response
    query = "Where is chunk C?"
    dummy_query_vector = embeddings[2]  # Query matches Chunk C perfectly
    
    with patch("app.vectorstore.faiss.embedding_service.get_query_embedding", return_value=dummy_query_vector):
        results = service.similarity_search(query, k=2)
        
    assert len(results) == 2
    # The first match should be Chunk C (distance should be close to 0)
    assert results[0]["document_id"] == "doc-B"
    assert results[0]["text"] == "This is chunk C"
    assert results[0]["score"] < 0.01  # Perfect similarity match distance should be ~0
    
    # 4. Remove Document A
    service.remove_document("doc-A")
    assert service.index.ntotal == 1
    assert len(service.metadata) == 1
    assert "0" not in service.metadata
    assert "2" in service.metadata  # Document B should remain untouched
    
    # Search after delete
    with patch("app.vectorstore.faiss.embedding_service.get_query_embedding", return_value=dummy_query_vector):
        results = service.similarity_search(query, k=2)
    assert len(results) == 1
    assert results[0]["document_id"] == "doc-B"
