#!/usr/bin/env python3
"""
Ingest documents into Redis vector database.

This script:
1. Extracts text from documents (PDF, TXT, MD)
2. Chunks the text into manageable pieces
3. Generates embeddings for each chunk
4. Stores everything in Redis with a vector index

Usage:
    python ingest.py document.pdf           # Ingest a PDF
    python ingest.py document.txt           # Ingest a text file
    python ingest.py doc1.pdf doc2.txt      # Ingest multiple files
    python ingest.py --flush document.pdf   # Clear database before ingesting
    python ingest.py --preview document.pdf # Preview chunks without storing
"""

import sys
from pathlib import Path

from redis_client import get_redis_client, flush_database
from extract_text import extract_text
from chunker import chunk_document, deduplicate_chunks
from embeddings import generate_embeddings
from indexer import store_chunks, get_index_info
from models import DocumentChunk


def process_document(file_path: str | Path) -> list[DocumentChunk]:
    """
    Extract and chunk a single document.
    
    Args:
        file_path: Path to the document.
        
    Returns:
        list[DocumentChunk]: List of document chunks.
    """
    file_path = Path(file_path)
    
    print(f"\n{'='*60}")
    print(f"STEP 1: Extracting and Chunking")
    print('='*60)
    
    # Extract text
    print(f"  Extracting text from '{file_path.name}'...")
    text = extract_text(file_path)
    print(f"  ✓ Extracted {len(text):,} characters")
    
    # Chunk the text
    print(f"  Chunking text...")
    chunks = chunk_document(text, source_file=file_path.name)
    print(f"  ✓ Created {len(chunks)} chunks")
    
    # Deduplicate
    unique_chunks = deduplicate_chunks(chunks)
    if len(unique_chunks) < len(chunks):
        print(f"  ✓ {len(unique_chunks)} unique chunks after deduplication")
    
    return unique_chunks


def preview_chunks(chunks: list[DocumentChunk], count: int = 5) -> None:
    """Preview the first N chunks."""
    print(f"\n{'='*60}")
    print(f"PREVIEW: First {min(count, len(chunks))} chunks")
    print('='*60)
    
    for chunk in chunks[:count]:
        print(f"\n--- Chunk {chunk.chunk_index} ---")
        print(f"Source: {chunk.source_file}")
        print(f"ID: {chunk.id}")
        print(f"Content preview: {chunk.content[:300]}...")
        print(f"Embed text preview: {chunk.to_embed_text()[:300]}...")


def main(file_paths: list[str], flush: bool = False, preview: bool = False) -> None:
    """
    Main ingestion pipeline.
    
    Args:
        file_paths: Paths to documents to ingest.
        flush: If True, flush database before ingesting.
        preview: If True, only preview chunks without storing.
    """
    if not file_paths:
        print("Error: No files specified.")
        print(__doc__)
        sys.exit(1)
    
    print("\n" + "="*60)
    print("REDIS VECTOR DATABASE INGESTION")
    print("="*60)
    print(f"Files: {', '.join(file_paths)}")
    
    # Verify files exist
    for fp in file_paths:
        if not Path(fp).exists():
            print(f"\n✗ Error: File not found: {fp}")
            sys.exit(1)
    
    # Process all documents
    all_chunks = []
    for file_path in file_paths:
        chunks = process_document(file_path)
        all_chunks.extend(chunks)
    
    print(f"\n  Total chunks from all files: {len(all_chunks)}")
    
    # Preview mode - show chunks and exit
    if preview:
        preview_chunks(all_chunks, count=5)
        print(f"\n✓ Preview complete. {len(all_chunks)} chunks parsed.")
        print("  Run without --preview to ingest into Redis.")
        return
    
    # Connect to Redis
    print("\nConnecting to Redis...")
    client = get_redis_client()
    
    # Optionally flush database
    if flush:
        flush_database(client, confirm=True)
    
    # Generate embeddings
    print(f"\n{'='*60}")
    print("STEP 2: Generating Embeddings")
    print('='*60)
    embeddings = generate_embeddings(all_chunks)
    
    # Store in Redis
    store_chunks(client, all_chunks, embeddings)
    
    # Show final status
    info = get_index_info(client)
    print(f"\n{'='*60}")
    print("INGESTION COMPLETE")
    print('='*60)
    print(f"  Index: {info['index_name']}")
    print(f"  Documents: {info['num_docs']}")
    print("\nYou can now run queries using: python query.py \"your search query\"")


if __name__ == "__main__":
    # Parse command line arguments
    file_paths = []
    flush = False
    preview = False
    
    for arg in sys.argv[1:]:
        if arg == "--flush":
            flush = True
        elif arg == "--preview":
            preview = True
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
        else:
            file_paths.append(arg)
    
    main(file_paths=file_paths, flush=flush, preview=preview)
