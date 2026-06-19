import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from app.embeddings import embedding_service
from app.embeddings.bge import EmbeddingService

def test_singleton_architecture():
    # Verify that importing from the package gives the same instance
    from app.embeddings import embedding_service as inst1
    from app.embeddings.bge import embedding_service as inst2
    assert inst1 is inst2

@patch("app.embeddings.bge.SentenceTransformer")
def test_lazy_loading_and_single_instantiation(mock_sentence_transformer):
    # Create new instance to avoid using the module-level loaded one
    service = EmbeddingService()
    assert service._model is None
    
    # Access the model property to trigger load
    model_inst = service.model
    assert service._model is not None
    mock_sentence_transformer.assert_called_once_with("BAAI/bge-small-en-v1.5", device="cpu")
    
    # Access it again and assert model constructor is not called again
    model_inst2 = service.model
    assert model_inst is model_inst2
    mock_sentence_transformer.assert_called_once()

@patch("app.embeddings.bge.SentenceTransformer")
def test_get_embeddings_shapes(mock_sentence_transformer):
    # Set up mock encoder output
    mock_model = MagicMock()
    mock_encoder = MagicMock(return_value=np.zeros((2, 384), dtype=np.float32))
    mock_model.encode = mock_encoder
    
    service = EmbeddingService()
    service._model = mock_model  # Inject mock model directly
    
    # Get embeddings for 2 text strings
    texts = ["Chunk number 1", "Chunk number 2"]
    vectors = service.get_embeddings(texts)
    
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32
    
    # Verify normalized and batch parameters passed correctly
    mock_encoder.assert_called_once_with(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        device="cpu"
    )

@patch("app.embeddings.bge.SentenceTransformer")
def test_get_query_embedding_shapes(mock_sentence_transformer):
    mock_model = MagicMock()
    mock_encoder = MagicMock(return_value=np.zeros((384,), dtype=np.float32))
    mock_model.encode = mock_encoder
    
    service = EmbeddingService()
    service._model = mock_model
    
    query = "Search document context"
    vector = service.get_query_embedding(query)
    
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (384,)
    
    # Verify query prefix prepended
    expected_prefixed_query = "Represent this sentence for searching relevant passages: Search document context"
    mock_encoder.assert_called_once_with(
        expected_prefixed_query,
        show_progress_bar=False,
        normalize_embeddings=True,
        device="cpu"
    )
