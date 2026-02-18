"""
Text chunking utilities.

Splits documents into overlapping chunks for embedding.
"""

from pathlib import Path
from models import DocumentChunk
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into overlapping chunks by words.
    
    Args:
        text: The full text to chunk.
        chunk_size: Maximum words per chunk.
        overlap: Number of overlapping words between chunks.
        
    Returns:
        list[str]: List of text chunks.
    """
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        return [text.strip()] if text.strip() else []
    
    step = chunk_size - overlap
    
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
        
        # Stop if we've captured all words
        if i + chunk_size >= len(words):
            break
    
    return chunks


def chunk_document(
    text: str,
    source_file: str | Path,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    metadata: dict = None,
) -> list[DocumentChunk]:
    """
    Split a document into DocumentChunk objects.
    
    Args:
        text: Full document text.
        source_file: Original filename.
        chunk_size: Maximum words per chunk.
        overlap: Overlapping words between chunks.
        metadata: Optional metadata to attach to all chunks.
        
    Returns:
        list[DocumentChunk]: List of document chunks ready for embedding.
    """
    source_file = Path(source_file).name if isinstance(source_file, Path) else Path(source_file).name
    text_chunks = chunk_text(text, chunk_size, overlap)
    
    chunks = []
    for i, content in enumerate(text_chunks):
        chunk = DocumentChunk.create(
            content=content,
            source_file=source_file,
            chunk_index=i,
            metadata=metadata or {},
        )
        chunks.append(chunk)
    
    return chunks


def deduplicate_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """
    Remove duplicate chunks based on content hash.
    
    Args:
        chunks: List of DocumentChunk objects.
        
    Returns:
        list[DocumentChunk]: Deduplicated list.
    """
    seen_hashes = set()
    unique = []
    
    for chunk in chunks:
        h = chunk.content_hash()
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(chunk)
    
    return unique
