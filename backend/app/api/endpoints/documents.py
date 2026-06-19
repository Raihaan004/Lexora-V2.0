from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas import DocumentResponse
from app.loaders import DocumentManager
from typing import List

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, TXT, CSV), validate the format,
    save it locally to storage, and return its metadata.
    """
    return DocumentManager.save_file(file)

@router.get("/", response_model=List[DocumentResponse])
async def list_documents():
    """
    List all uploaded documents and their status.
    """
    return DocumentManager.list_all()

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from storage and the local registry.
    """
    success = DocumentManager.delete_file(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": f"Document {document_id} deleted successfully."}

