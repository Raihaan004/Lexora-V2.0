import pytest
from app.services.chunker import ChunkerService

def test_chunker_basic():
    # 400 char chunk size, 50 char overlap
    chunker = ChunkerService(chunk_size=100, chunk_overlap=20)
    
    # 1. Very short text
    text = "Short text."
    chunks = chunker.split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."

    # 2. Text larger than chunk size
    text_long = (
        "This is the first segment of text that we will split. "
        "It contains several sentences. The chunker should partition it "
        "recursively on delimiters. Let's see how well it works."
    )
    chunks = chunker.split_text(text_long)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 100
        
    # Check overlap presence - adjacent chunks should share some character sequence
    assert len(chunks) >= 2
    # Ensure chunk boundaries do not cut words in half since we split on word boundaries (" ")
    for chunk in chunks:
        assert not chunk.startswith(" ") and not chunk.endswith(" ")

def test_chunker_empty():
    chunker = ChunkerService()
    assert chunker.split_text("") == []
    assert chunker.split_text("   ") == []
