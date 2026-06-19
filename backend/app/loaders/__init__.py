# Document loading and parsing package
from app.loaders.base import BaseLoader
from app.loaders.pdf import PDFLoader
from app.loaders.docx import DOCXLoader
from app.loaders.txt import TXTLoader
from app.loaders.csv import CSVLoader
from app.loaders.manager import DocumentManager

def get_loader_for_extension(ext: str) -> BaseLoader:
    """Factory helper to fetch corresponding BaseLoader subclass by extension."""
    ext = ext.lower()
    if ext == ".pdf":
        return PDFLoader()
    elif ext == ".docx":
        return DOCXLoader()
    elif ext == ".txt":
        return TXTLoader()
    elif ext == ".csv":
        return CSVLoader()
    else:
        raise ValueError(f"No document loader configured for extension '{ext}'")
