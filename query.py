#!/usr/bin/env python3
"""
Query the Redis vector database for similar documents.

Usage:
    python query.py "Chinese Military Helicopters"
    python query.py "electronic warfare systems" --top-k 10
    python query.py --interactive
"""

import sys

from config import DEFAULT_TOP_K
from redis_client import get_redis_client
from search import search, format_results
from indexer import get_index_info


def run_query(query_text: str, top_k: int = DEFAULT_TOP_K) -> None:
    """
    Run a single search query and display results.
    
    Args:
        query_text: The search query.
        top_k: Number of results to return.
    """
    print(f"\n{'='*60}")
    print("VECTOR SIMILARITY SEARCH")
    print('='*60)
    print(f"Query: \"{query_text}\"")
    print(f"Top K: {top_k}")
    
    # Connect to Redis
    client = get_redis_client()
    
    # Check index exists
    info = get_index_info(client)
    if info.get("num_docs", 0) == 0:
        print("\n✗ Error: No documents in index. Run ingest.py first.")
        sys.exit(1)
    
    print(f"Searching {info['num_docs']} documents...")
    
    # Perform search
    results = search(client, query_text, top_k=top_k)
    
    # Display results
    print(format_results(results))


def interactive_mode() -> None:
    """
    Run in interactive mode for multiple queries.
    """
    print("\n" + "="*60)
    print("INTERACTIVE VECTOR SEARCH")
    print("="*60)
    print("Type your queries below. Enter 'quit' or 'exit' to stop.\n")
    
    # Connect once
    client = get_redis_client()
    
    info = get_index_info(client)
    print(f"Index contains {info.get('num_docs', 0)} documents.\n")
    
    while True:
        try:
            query = input("Query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not query:
            continue
        
        if query.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # Check for top_k override (e.g., "helicopters --top-k 3")
        top_k = DEFAULT_TOP_K
        if "--top-k" in query:
            parts = query.split("--top-k")
            query = parts[0].strip()
            try:
                top_k = int(parts[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        # Run search
        from search import search, format_results
        results = search(client, query, top_k=top_k)
        print(format_results(results))
        print()


def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = sys.argv[1:]
    
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        if not args:
            print("\nNo query provided. Use --interactive for interactive mode.")
        sys.exit(0)
    
    if "--interactive" in args or "-i" in args:
        interactive_mode()
        return
    
    # Extract query and options
    top_k = DEFAULT_TOP_K
    query_parts = []
    
    i = 0
    while i < len(args):
        if args[i] == "--top-k" and i + 1 < len(args):
            try:
                top_k = int(args[i + 1])
            except ValueError:
                print(f"Invalid --top-k value: {args[i + 1]}")
                sys.exit(1)
            i += 2
        else:
            query_parts.append(args[i])
            i += 1
    
    query_text = " ".join(query_parts)
    
    if not query_text:
        print("Error: No query provided.")
        sys.exit(1)
    
    run_query(query_text, top_k=top_k)


if __name__ == "__main__":
    main()
