import fitz  # PyMuPDF
from pathlib import Path
from app.loaders.base import BaseLoader

class PDFLoader(BaseLoader):
    """Parses PDF documents offline using PyMuPDF."""

    def load(self, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {file_path}")
            
        text_content = []
        try:
            # Open PDF file offline
            with fitz.open(file_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"Failed to parse PDF: File is encrypted/password-protected: {file_path.name}")
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        text_content.append(page_text)
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise e
            raise RuntimeError(f"Error reading PDF '{file_path.name}': {str(e)}")
            
        # Join pages and clean up multiple consecutive whitespaces/newlines
        raw_text = "\n\n".join(text_content)
        cleaned_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return "\n".join(cleaned_lines)
