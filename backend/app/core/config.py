import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lexora"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR.parent / "storage"
    
    DOCUMENTS_DIR: Path = STORAGE_DIR / "documents"
    FAISS_DIR: Path = STORAGE_DIR / "faiss"
    METADATA_DIR: Path = STORAGE_DIR / "metadata"

    # AI Configurations
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen3:4b"
    EMBEDDING_MODEL: str = "bge-m3"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
os.makedirs(settings.FAISS_DIR, exist_ok=True)
os.makedirs(settings.METADATA_DIR, exist_ok=True)
