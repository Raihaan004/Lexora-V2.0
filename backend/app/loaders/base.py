from abc import ABC, abstractmethod
from pathlib import Path

class BaseLoader(ABC):
    """Abstract base class for all file-type specific document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> str:
        """
        Parses a document file and returns its clean raw text.
        
        Args:
            file_path: Absolute Path object to the target file.
            
        Returns:
            clean_text: The extracted and sanitized plain text.
            
        Raises:
            Exception: If parsing fails or the file is corrupted.
        """
        pass
