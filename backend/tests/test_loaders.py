import pytest
import os
import pandas as pd
import fitz
import docx
from pathlib import Path
from app.loaders import get_loader_for_extension, PDFLoader, DOCXLoader, TXTLoader, CSVLoader

def test_txt_loader(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello\n\n  World!  \n", encoding="utf-8")
    
    loader = get_loader_for_extension(".txt")
    assert isinstance(loader, TXTLoader)
    text = loader.load(file_path)
    assert text == "Hello\nWorld!"

def test_csv_loader(tmp_path):
    file_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        "Name": ["Alice", "Bob"],
        "Age": [25, 30]
    })
    df.to_csv(file_path, index=False)
    
    loader = get_loader_for_extension(".csv")
    assert isinstance(loader, CSVLoader)
    text = loader.load(file_path)
    # Check rows are mapped into descriptions
    assert "Row 1:" in text
    assert "Name: Alice" in text
    assert "Age: 25" in text
    assert "Row 2:" in text
    assert "Name: Bob" in text
    assert "Age: 30" in text

def test_pdf_loader(tmp_path):
    file_path = tmp_path / "test.pdf"
    # Generate simple PDF using PyMuPDF (fitz)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "PDF Offline Text Extraction")
    doc.save(file_path)
    doc.close()
    
    loader = get_loader_for_extension(".pdf")
    assert isinstance(loader, PDFLoader)
    text = loader.load(file_path)
    assert text == "PDF Offline Text Extraction"

def test_docx_loader(tmp_path):
    file_path = tmp_path / "test.docx"
    # Generate simple docx document using python-docx
    doc = docx.Document()
    doc.add_paragraph("Word Offline Text Extraction")
    doc.save(file_path)
    
    loader = get_loader_for_extension(".docx")
    assert isinstance(loader, DOCXLoader)
    text = loader.load(file_path)
    assert text == "Word Offline Text Extraction"
