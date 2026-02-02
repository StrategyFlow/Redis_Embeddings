#!/usr/bin/env python3
"""
Ingest PDF documents into Redis vector database.

This script:
1. Extracts and parses structured data from a PDF
2. Deduplicates entries
3. Generates embeddings for each entry
4. Stores everything in Redis with a vector index

Usage:
    python ingest.py                    # Use default PDF from config
    python ingest.py path/to/file.pdf   # Use specified PDF
    python ingest.py --flush            # Clear database before ingesting
    python ingest.py --preview          # Preview parsed entries without storing
"""

import sys
from pathlib import Path

from config import PDF_FILE_PATH
from redis_client import get_redis_client, flush_database
from parser import parse_pdf, preview_entries
from embeddings import generate_embeddings
from indexer import store_entries, get_index_info


def main(pdf_path: str | None = None, flush: bool = False, preview: bool = False) -> None:
    """
    Main ingestion pipeline.
    
    Args:
        pdf_path: Path to PDF file. Defaults to config value.
        flush: If True, flush database before ingesting.
        preview: If True, only preview parsed entries without storing.
    """
    pdf_path = pdf_path or PDF_FILE_PATH
    
    print("\n" + "="*60)
    print("REDIS VECTOR DATABASE INGESTION")
    print("="*60)
    print(f"PDF: {pdf_path}")
    
    # Verify PDF exists
    if not Path(pdf_path).exists():
        print(f"\n✗ Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Parse PDF into structured entries
    entries = parse_pdf(pdf_path)
    
    # Preview mode - show entries and exit
    if preview:
        preview_entries(entries, count=10)
        print(f"\n✓ Preview complete. {len(entries)} entries parsed.")
        print("  Run without --preview to ingest into Redis.")
        return
    
    # Connect to Redis
    print("\nConnecting to Redis...")
    client = get_redis_client()
    
    # Optionally flush database
    if flush:
        flush_database(client, confirm=True)
    
    # Generate embeddings
    embeddings = generate_embeddings(entries)
    
    # Store in Redis
    store_entries(client, entries, embeddings)
    
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
    pdf_path = None
    flush = False
    preview = False
    
    for arg in sys.argv[1:]:
        if arg == "--flush":
            flush = True
        elif arg == "--preview":
            preview = True
        elif arg.endswith(".pdf"):
            pdf_path = arg
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
    
    main(pdf_path=pdf_path, flush=flush, preview=preview)
