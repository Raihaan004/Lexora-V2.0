import docx
from pathlib import Path
from app.loaders.base import BaseLoader

class DOCXLoader(BaseLoader):
    """Parses Word documents (.docx) offline using python-docx."""

    def load(self, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"DOCX file not found at: {file_path}")
            
        try:
            doc = docx.Document(file_path)
            paragraphs_text = []
            
            # Extract paragraph text
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs_text.append(para.text)
                    
            # Extract table cell texts if any are present
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        paragraphs_text.append(" | ".join(row_text))
                        
            cleaned_text = "\n".join(paragraphs_text)
            return cleaned_text
            
        except Exception as e:
            raise RuntimeError(f"Error reading DOCX '{file_path.name}': {str(e)}")
