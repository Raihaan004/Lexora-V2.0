import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from app.core.config import settings
from app.loaders.manager import METADATA_FILE

def clean_test_directories():
    """Cleanup test files and registries generated during testing."""
    if settings.DOCUMENTS_DIR.exists():
        for f in settings.DOCUMENTS_DIR.iterdir():
            if f.is_file():
                try:
                    os.remove(f)
                except Exception:
                    pass
    if METADATA_FILE.exists():
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["offline"] is True

def test_document_upload_and_delete_flow(client: TestClient):
    clean_test_directories()
    
    # 1. Upload valid text file
    file_content = b"Lexora test offline assistant document content."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_doc.txt", file_content, "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_doc.txt"
    assert data["status"] == "completed"
    doc_id = data["id"]
    
    # Verify file saved on disk
    stored_path = settings.DOCUMENTS_DIR / f"{doc_id}.txt"
    assert stored_path.exists()
    assert stored_path.read_bytes() == file_content
    
    # 2. Upload invalid file format
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invalid_image.png", b"fake-png-data", "image/png")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    
    # 3. List documents
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id
    
    # 4. Delete document
    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Document {doc_id} deleted successfully."
    
    # Verify file removed from disk and registry
    assert not stored_path.exists()
    response = client.get("/api/v1/documents/")
    assert len(response.json()) == 0
    
    # 5. Delete non-existent document
    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"

    clean_test_directories()
