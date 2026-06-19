import os
import faiss
import numpy as np
import json
from typing import List, Dict, Any
from app.core.config import settings
from app.embeddings import embedding_service

class FAISSService:
    """
    Service wrapper managing local FAISS database operations.
    Loads FAISS index from disk lazily to avoid startup crashes if Ollama is offline.
    """
    def __init__(self):
        self.index_path = settings.FAISS_DIR / "index.faiss"
        self.metadata_path = settings.METADATA_DIR / "vector_chunks.json"
        self.index = None
        self.metadata: Dict[str, Any] = {}
        
        # Load index on instance initialization (only once at startup)
        self._load_store()

    def _load_store(self):
        """Loads FAISS index and metadata registry from storage/ if they exist."""
        os.makedirs(settings.FAISS_DIR, exist_ok=True)
        os.makedirs(settings.METADATA_DIR, exist_ok=True)
        
        # Read or initialize FAISS Index
        if self.index_path.exists():
            try:
                # Read index containing structural ID maps (auto-detects dimensions)
                self.index = faiss.read_index(str(self.index_path))
            except Exception:
                # Reset if file is corrupted
                self.index = None
        else:
            self.index = None

        # Read or initialize metadata
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}
        else:
            self.metadata = {}

    def save_store(self):
        """Saves current index and metadata map to storage directories."""
        os.makedirs(settings.FAISS_DIR, exist_ok=True)
        os.makedirs(settings.METADATA_DIR, exist_ok=True)
        
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
            
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=4, ensure_ascii=False)

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        """
        Adds vector embeddings and metadata chunks to the index.
        Saves changes to disk immediately.
        
        Args:
            chunks: List of metadata dictionaries (text, file reference, chunk index).
            embeddings: Numpy array of shape (N, D).
        """
        if not chunks or len(chunks) == 0:
            return
            
        # Lazy initialize index based on input vector dimension (e.g. 1024 or 768)
        if self.index is None:
            dimension = embeddings.shape[1]
            flat_index = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIDMap(flat_index)
            
        # Determine starting custom ID for index
        if self.metadata:
            start_id = max(int(k) for k in self.metadata.keys()) + 1
        else:
            start_id = 0
            
        # Create unique long-integer IDs for FAISS IndexIDMap
        ids = np.arange(start_id, start_id + len(chunks), dtype=np.int64)
        
        # Add to index with custom ID registry mapping
        self.index.add_with_ids(embeddings, ids)
        
        # Save mapping reference
        for vector_id, chunk_data in zip(ids, chunks):
            self.metadata[str(vector_id)] = chunk_data
            
        # Write state to disk
        self.save_store()

    def remove_document(self, document_id: str):
        """
        Removes all vector points and metadata associated with a deleted document.
        
        Args:
            document_id: UUID of document to remove.
        """
        if self.index is None:
            return
            
        ids_to_remove = []
        for vector_id, chunk in list(self.metadata.items()):
            if chunk.get("document_id") == document_id:
                ids_to_remove.append(int(vector_id))
                
        if ids_to_remove:
            # Delete from FAISS IndexIDMap
            ids_arr = np.array(ids_to_remove, dtype=np.int64)
            self.index.remove_ids(ids_arr)
            
            # Clean up metadata dictionary
            for vector_id in ids_to_remove:
                self.metadata.pop(str(vector_id), None)
                
            self.save_store()

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Performs L2 distance similarity search on the local index.
        
        Args:
            query: User prompt query string.
            k: Maximum matching count.
            
        Returns:
            results: List of matching text chunks.
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        # Generate query vector (resolves dimension size dynamically via Ollama API)
        query_vec = embedding_service.get_query_embedding(query)
        # Reshape to 2D shape (1, D)
        query_vec_2d = np.array([query_vec], dtype=np.float32)
        
        # Search FAISS Index
        distances, indices = self.index.search(query_vec_2d, k)
        
        results = []
        for dist, vector_id in zip(distances[0], indices[0]):
            if vector_id == -1:  # Sentinel value from FAISS representing no match
                continue
                
            vid_str = str(vector_id)
            if vid_str in self.metadata:
                match_chunk = self.metadata[vid_str].copy()
                match_chunk["score"] = float(dist)
                results.append(match_chunk)
                
        return results

# Expose as a module-level singleton instance
vector_store_service = FAISSService()
