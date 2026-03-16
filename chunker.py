"""
Smart text chunking utilities.

Combines header detection with entity extraction for context-aware chunking.
Works across different document types.
"""

import re
from pathlib import Path
from models import DocumentChunk
from config import CHUNK_SIZE, CHUNK_OVERLAP


# =============================================================================
# Header Detection
# =============================================================================
def is_likely_header(line: str) -> bool:
    """
    Heuristic to detect section headers.
    
    Matches:
    - Short lines in ALL CAPS
    - Lines ending with colon
    - Numbered sections (1. Introduction, 2.1 Background)
    - Lines with equipment-style names (Bell 205, UH-60L, T-72)
    """
    line = line.strip()
    if not line or len(line) > 150:
        return False
    
    # All caps (at least 3 words)
    if line.isupper() and len(line.split()) >= 2:
        return True
    
    # Ends with colon
    if line.endswith(':') and len(line) < 80:
        return True
    
    # Numbered section
    if re.match(r'^\d+\.?\d*\s+[A-Z]', line):
        return True
    
    # Equipment-style header (e.g., "Bell 205 American Utility Helicopter")
    if re.match(r'^[A-Z][A-Za-z0-9\-]+\s+\d*\s*[A-Z][a-z]+', line) and len(line) < 100:
        return True
    
    # WEG-style entry
    if 'WEG Location:' in line or re.match(r'^[A-Z][A-Za-z0-9\-/]+\s+(American|Russian|Chinese|German|French|British)', line):
        return True
    
    return False


def has_clear_headers(text: str) -> bool:
    """Check if document has detectable header structure."""
    lines = text.split('\n')
    header_count = sum(1 for line in lines if is_likely_header(line))
    # Consider structured if >2 headers found
    return header_count > 2


# =============================================================================
# Entity Extraction
# =============================================================================
def extract_key_entities(text: str) -> list[str]:
    """Extract entities using SpaCy."""
    try:
        from military_ner import extract_entities
        ents = extract_entities(text)
        # Prioritize KB-linked entities
        kb_ents = [e['text'] for e in ents if e.get('kb_id')]
        other_ents = [e['text'] for e in ents if not e.get('kb_id')]
        return (kb_ents + other_ents)[:5]
    except Exception as e:
        print(f"  Entity extraction unavailable: {e}")
        return []


# =============================================================================
# Chunking Strategies
# =============================================================================
def chunk_with_inherited_context(
    text: str,
    source_file: str,
    chunk_size: int = CHUNK_SIZE,
) -> list[DocumentChunk]:
    """
    Chunk structured documents, propagating headers to child chunks.
    """
    lines = text.split('\n')
    chunks = []
    current_header = ""
    buffer = []
    buffer_words = 0
    chunk_index = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        if is_likely_header(line_stripped):
            # Flush buffer with previous header
            if buffer:
                content = '\n'.join(buffer).strip()
                if content:
                    if current_header:
                        content = f"{current_header}\n\n{content}"
                    chunks.append(DocumentChunk.create(
                        content=content,
                        source_file=source_file,
                        chunk_index=chunk_index,
                        metadata={"header": current_header},
                    ))
                    chunk_index += 1
                buffer = []
                buffer_words = 0
            current_header = line_stripped
        else:
            line_words = len(line_stripped.split())
            
            # Check if buffer is getting too large
            if buffer_words + line_words > chunk_size and buffer:
                content = '\n'.join(buffer).strip()
                if content:
                    if current_header:
                        content = f"{current_header}\n\n{content}"
                    chunks.append(DocumentChunk.create(
                        content=content,
                        source_file=source_file,
                        chunk_index=chunk_index,
                        metadata={"header": current_header},
                    ))
                    chunk_index += 1
                buffer = []
                buffer_words = 0
            
            if line_stripped:
                buffer.append(line_stripped)
                buffer_words += line_words
    
    # Flush remaining buffer
    if buffer:
        content = '\n'.join(buffer).strip()
        if content:
            if current_header:
                content = f"{current_header}\n\n{content}"
            chunks.append(DocumentChunk.create(
                content=content,
                source_file=source_file,
                chunk_index=chunk_index,
                metadata={"header": current_header},
            ))
    
    return chunks


def chunk_with_entity_prefix(
    text: str,
    source_file: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """
    Chunk unstructured documents, prepending extracted entities for context.
    """
    # Basic word-based chunking
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        raw_chunks = [text.strip()] if text.strip() else []
    else:
        raw_chunks = []
        step = chunk_size - overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                raw_chunks.append(chunk.strip())
            if i + chunk_size >= len(words):
                break
    
    # Enrich each chunk with entities
    for i, chunk in enumerate(raw_chunks):
        entities = extract_key_entities(chunk)
        
        if entities:
            prefix = f"Context: {', '.join(entities)}\n\n"
            content = prefix + chunk
        else:
            content = chunk
        
        chunks.append(DocumentChunk.create(
            content=content,
            source_file=source_file,
            chunk_index=i,
            metadata={"entities": entities},
        ))
    
    return chunks


# =============================================================================
# Main Smart Chunking Function
# =============================================================================
def smart_chunk(
    text: str,
    source_file: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """
    Intelligently chunk documents based on detected structure.
    
    - Uses header propagation for structured documents
    - Uses entity prefixing for unstructured documents
    
    Args:
        text: Document text
        source_file: Source filename
        chunk_size: Target words per chunk
        overlap: Word overlap (for unstructured chunking)
        
    Returns:
        list[DocumentChunk]: Contextually-enriched chunks
    """
    if not text.strip():
        return []
    
    # Detect document structure
    if has_clear_headers(text):
        print(f"  Detected structured document → using header propagation")
        chunks = chunk_with_inherited_context(text, source_file, chunk_size)
    else:
        print(f"  Detected unstructured document → using entity prefixing")
        chunks = chunk_with_entity_prefix(text, source_file, chunk_size, overlap)
    
    return chunks


# =============================================================================
# Main Entry Point
# =============================================================================
def chunk_document(
    text: str,
    source_file: str | Path,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    metadata: dict = None,
) -> list[DocumentChunk]:
    """
    Main entry point for chunking (updated to use smart chunking).
    """
    source_file = Path(source_file).name if isinstance(source_file, Path) else Path(source_file).name
    
    # Use smart chunking
    chunks = smart_chunk(text, source_file, chunk_size, overlap)
    
    # Add any additional metadata
    if metadata:
        for chunk in chunks:
            chunk.metadata.update(metadata)
    
    return chunks


def deduplicate_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """
    Remove duplicate chunks based on content hash.
    """
    seen_hashes = set()
    unique = []
    
    for chunk in chunks:
        h = chunk.content_hash()
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(chunk)
    
    return unique