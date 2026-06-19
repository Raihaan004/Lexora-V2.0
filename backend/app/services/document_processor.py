import fitz  # PyMuPDF
import docx
from typing import List, Dict, Any
from pathlib import Path

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: Path) -> str:
        """
        Detects document type and extracts text offline.
        Supports PDF, DOCX, and TXT files.
        """
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return DocumentProcessor._extract_pdf(file_path)
        elif ext == ".docx":
            return DocumentProcessor._extract_docx(file_path)
        elif ext == ".txt":
            return DocumentProcessor._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        text = ""
        # Open PDF file offline using fitz (PyMuPDF)
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def _extract_docx(file_path: Path) -> str:
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    @staticmethod
    def _extract_txt(file_path: Path) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Splits text into chunks of specified characters, with overlap.
        """
        # TODO: Implement a clean recursive or sliding window text splitter
        chunks = []
        return chunks

    @staticmethod
    def process_file(file_path: Path, document_id: str) -> List[Dict[str, Any]]:
        """
        Extracts, chunks, and formats document data with metadata attributes.
        """
        raw_text = DocumentProcessor.extract_text(file_path)
        text_chunks = DocumentProcessor.split_text(raw_text)
        
        chunks_metadata = []
        for idx, chunk in enumerate(text_chunks):
            chunks_metadata.append({
                "id": f"{document_id}_{idx}",
                "document_id": document_id,
                "filename": file_path.name,
                "text": chunk,
                "chunk_index": idx
            })
        return chunks_metadata
