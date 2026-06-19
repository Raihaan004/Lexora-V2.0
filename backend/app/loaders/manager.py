import os
import uuid
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.schemas.document import DocumentResponse

METADATA_FILE = settings.METADATA_DIR / "documents.json"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv"}

def get_document_metadata() -> Dict[str, Any]:
    """Reads document registry metadata from disk."""
    if not METADATA_FILE.exists():
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_document_metadata(metadata: Dict[str, Any]):
    """Writes document registry metadata to disk."""
    os.makedirs(settings.METADATA_DIR, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, default=str)

class DocumentManager:
    @staticmethod
    def validate_file(filename: str) -> str:
        """Validates file extension. Returns lowercase extension if valid, else raises HTTPException."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{ext}'. Supported types are: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        return ext

    @staticmethod
    def save_file(upload_file: UploadFile) -> DocumentResponse:
        """
        Validates, saves the file to storage/documents/ using a generated UUID,
        updates the local documents registry, and returns document metadata.
        """
        ext = DocumentManager.validate_file(upload_file.filename)
        
        # Generate clean ID and safe filename
        doc_id = str(uuid.uuid4())
        stored_filename = f"{doc_id}{ext}"
        destination_path = settings.DOCUMENTS_DIR / stored_filename
        
        # Create storage folder if missing
        os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
        
        # Stream save file to disk
        file_size = 0
        try:
            with open(destination_path, "wb") as buffer:
                # Read chunks to handle large files efficiently
                while chunk := upload_file.file.read(8192):
                    buffer.write(chunk)
                    file_size += len(chunk)
        except Exception as e:
            # Cleanup if save failed
            if destination_path.exists():
                os.remove(destination_path)
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Extract text and split into chunks
        chunk_count = 0
        try:
            from app.loaders import get_loader_for_extension
            loader = get_loader_for_extension(ext)
            extracted_text = loader.load(destination_path)
            
            from app.services.chunker import chunker_service
            chunks = chunker_service.split_text(extracted_text)
            chunk_count = len(chunks)
            
            # Save chunks to storage/metadata/<doc_id>_chunks.json
            chunks_path = settings.METADATA_DIR / f"{doc_id}_chunks.json"
            os.makedirs(settings.METADATA_DIR, exist_ok=True)
            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump({
                    "document_id": doc_id,
                    "filename": upload_file.filename,
                    "chunks": chunks
                }, f, indent=4, ensure_ascii=False)
                
            # Generate vector embeddings offline and register in FAISS
            if chunks:
                from app.embeddings import embedding_service
                embeddings = embedding_service.get_embeddings(chunks)
                
                from app.vectorstore import vector_store_service
                chunks_meta = []
                for i, chunk_text in enumerate(chunks):
                    chunks_meta.append({
                        "document_id": doc_id,
                        "filename": upload_file.filename,
                        "text": chunk_text,
                        "chunk_index": i
                    })
                vector_store_service.add_documents(chunks_meta, embeddings)
                
        except Exception as e:
            # Cleanup saved file on processing failure to avoid orphaned files
            if destination_path.exists():
                try:
                    os.remove(destination_path)
                except Exception:
                    pass
            # Also clean up FAISS references if indexing fails halfway
            try:
                from app.vectorstore import vector_store_service
                vector_store_service.remove_document(doc_id)
            except Exception:
                pass
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to process, chunk and index document: {str(e)}"
            )
        
        # Generate metadata entry
        now = datetime.now()
        doc_metadata = {
            "id": doc_id,
            "filename": upload_file.filename,
            "stored_filename": stored_filename,
            "file_size_bytes": file_size,
            "status": "completed",
            "chunk_count": chunk_count,
            "uploaded_at": now.isoformat(),
            "error_message": None
        }

        # Update registry
        registry = get_document_metadata()
        registry[doc_id] = doc_metadata
        save_document_metadata(registry)
        
        return DocumentResponse(**doc_metadata)

    @staticmethod
    def list_all() -> List[DocumentResponse]:
        """Lists all uploaded documents registered in the local metadata database."""
        registry = get_document_metadata()
        docs = []
        for doc_data in registry.values():
            docs.append(DocumentResponse(**doc_data))
        # Sort by upload date descending
        docs.sort(key=lambda x: x.uploaded_at, reverse=True)
        return docs

    @staticmethod
    def delete_file(doc_id: str) -> bool:
        """Removes the file and its chunks from disk and deletes its entry from the registry."""
        registry = get_document_metadata()
        if doc_id not in registry:
            return False
            
        doc_data = registry[doc_id]
        stored_filename = doc_data.get("stored_filename")
        
        # Remove physical file if it exists
        if stored_filename:
            file_path = settings.DOCUMENTS_DIR / stored_filename
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                    
        # Remove chunks metadata file if it exists
        chunks_path = settings.METADATA_DIR / f"{doc_id}_chunks.json"
        if chunks_path.exists():
            try:
                os.remove(chunks_path)
            except Exception:
                pass
                
        # Remove vectors from FAISS Index
        try:
            from app.vectorstore import vector_store_service
            vector_store_service.remove_document(doc_id)
        except Exception:
            pass
        
        # Remove metadata entry
        del registry[doc_id]
        save_document_metadata(registry)
        return True
