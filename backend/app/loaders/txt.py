from pathlib import Path
from app.loaders.base import BaseLoader

class TXTLoader(BaseLoader):
    """Parses plain text files offline using native Python file operations with robust encoding detection."""

    def load(self, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found at: {file_path}")
            
        encodings = ["utf-8", "latin-1", "utf-16", "cp1252"]
        last_error = None
        
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                    
                # Clean text: remove leading/trailing whitespaces and filter lines
                cleaned_lines = [line.strip() for line in content.splitlines() if line.strip()]
                return "\n".join(cleaned_lines)
                
            except UnicodeDecodeError as e:
                last_error = e
                continue
            except Exception as e:
                raise RuntimeError(f"Error reading text file '{file_path.name}': {str(e)}")
                
        raise RuntimeError(
            f"Failed to decode text file '{file_path.name}'. Tried encodings {encodings}. "
            f"Error: {str(last_error)}"
        )
