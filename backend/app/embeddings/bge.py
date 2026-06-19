import requests
import numpy as np
from typing import List
from app.core.config import settings

class EmbeddingService:
    """
    Embedding service that delegates vector generation to local Ollama instance.
    Bypasses local PyTorch DLL execution blocks on restricted Windows environments
    and eliminates heavy memory/startup times.
    """
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.EMBEDDING_MODEL
        self._dimension = None

    @property
    def dimension(self) -> int:
        """Lazy detects the vector dimension size from Ollama output on first call."""
        if self._dimension is None:
            # Query a dummy string to detect dimension size dynamically
            dummy_vec = self.get_query_embedding("test")
            self._dimension = len(dummy_vec)
        return self._dimension

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generates dense embedding vectors offline using Ollama /api/embed.
        
        Args:
            texts: List of split text strings.
            
        Returns:
            vectors: np.ndarray of shape (N, D) with float32 values.
        """
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
            
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model_name,
            "input": texts
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            
            if not embeddings:
                raise ValueError("Ollama returned empty embeddings array.")
                
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate embeddings from local Ollama: {str(e)}. "
                f"Please ensure Ollama is running (`ollama serve`) and you have pulled the model: `ollama pull {self.model_name}`"
            )

    def get_query_embedding(self, query: str) -> np.ndarray:
        """
        Generates an embedding vector offline for a single search query.
        
        Args:
            query: User search query string.
            
        Returns:
            vector: np.ndarray of shape (D,) with float32 values.
        """
        if not query or not query.strip():
            # Return a dummy vector if query is blank (fallback size 1024 or self._dimension)
            dim = self._dimension or 1024
            return np.zeros(dim, dtype=np.float32)
            
        prefixed_query = query.strip()
        # Some models perform better with retrieval search prefixes
        if "nomic" in self.model_name.lower():
            prefixed_query = f"search_query: {query.strip()}"
        elif "bge" in self.model_name.lower():
            # BGE M3 uses default prompts or runs without prefixes for dense retrieval
            pass
            
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.model_name,
            "input": [prefixed_query]
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            embeddings = data.get("embeddings", [])
            
            if not embeddings:
                raise ValueError("Ollama returned empty embeddings.")
                
            return np.array(embeddings[0], dtype=np.float32)
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate query embedding: {str(e)}. "
                f"Please ensure Ollama is running and has model pulled: `ollama pull {self.model_name}`"
            )

# Expose as a module-level singleton instance
embedding_service = EmbeddingService()
