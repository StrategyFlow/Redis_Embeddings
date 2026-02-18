"""
Document text extraction.

Handles loading text from various document formats.
Supports: .txt, .pdf, .md
"""

from pathlib import Path


def extract_text(file_path: str | Path) -> str:
    """
    Extract text from a document.
    
    Supports:
    - .txt files (direct read with encoding fallbacks)
    - .pdf files (using PyMuPDF/fitz)
    - .md files (direct read)
    
    Args:
        file_path: Path to the document.
        
    Returns:
        str: Extracted text content.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix == ".txt":
        return _extract_from_txt(file_path)
    elif suffix == ".pdf":
        return _extract_from_pdf(file_path)
    elif suffix == ".md":
        return _extract_from_txt(file_path)  # Same as txt
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_from_txt(file_path: Path) -> str:
    """Extract text from a .txt file, handling various encodings."""
    # Try common encodings in order
    encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Fallback: read with errors ignored
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF using PyMuPDF."""
    import fitz
    
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    
    return text
