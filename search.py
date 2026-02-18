"""
Vector similarity search functionality.

Handles querying the Redis index for similar documents.
"""

from dataclasses import dataclass

import numpy as np
import redis
from redis.commands.search.query import Query

from config import INDEX_NAME, DEFAULT_TOP_K
from embeddings import embed_query


@dataclass
class SearchResult:
    """Represents a single search result."""
    rank: int
    score: float  # Similarity score (0-1, higher is more similar)
    content: str
    source_file: str
    chunk_index: int
    doc_id: str
    metadata: str = ""


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Remove duplicate results based on content hash.
    
    Keeps the highest-scored result for each unique content.
    
    Args:
        results: List of search results (assumed sorted by score).
        
    Returns:
        list[SearchResult]: Deduplicated results with updated ranks.
    """
    seen_content = set()
    unique_results = []
    
    for result in results:
        # Use first 100 chars as a simple dedup key
        content_key = result.content[:100]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_results.append(result)
    
    # Re-rank after deduplication
    for i, result in enumerate(unique_results):
        result.rank = i + 1
    
    return unique_results


def search(
    client: redis.Redis,
    query_text: str,
    top_k: int = DEFAULT_TOP_K,
    return_fields: list[str] | None = None
) -> list[SearchResult]:
    """
    Perform a semantic similarity search.
    
    Args:
        client: Redis client instance.
        query_text: The search query.
        top_k: Number of results to return.
        return_fields: Fields to include in results. Defaults to all.
        
    Returns:
        list[SearchResult]: Ranked list of search results.
    """
    return_fields = return_fields or ["content", "source_file", "chunk_index", "metadata"]
    
    # Generate query embedding
    print(f"  Embedding query: '{query_text}'")
    query_vector = embed_query(query_text)
    query_vector_bytes = query_vector.tobytes()
    
    # Build KNN query - fetch extra to account for duplicates
    fetch_k = top_k * 3
    base_query = f"(*)=>[KNN {fetch_k} @vector $query_vec AS vector_score]"
    
    q = (
        Query(base_query)
        .sort_by("vector_score")
        .return_fields(*return_fields, "vector_score")
        .dialect(2)
    )
    
    # Execute search
    print(f"  Searching for top {top_k} results...")
    query_params = {"query_vec": query_vector_bytes}
    results = client.ft(INDEX_NAME).search(q, query_params)
    
    # Process results
    search_results = []
    for i, doc in enumerate(results.docs):
        # Convert distance to similarity (cosine distance -> similarity)
        distance = float(doc.vector_score)
        similarity = 1 - distance
        
        result = SearchResult(
            rank=i + 1,
            score=similarity,
            content=getattr(doc, "content", ""),
            source_file=getattr(doc, "source_file", "Unknown"),
            chunk_index=int(getattr(doc, "chunk_index", 0)),
            doc_id=doc.id,
            metadata=getattr(doc, "metadata", ""),
        )
        search_results.append(result)
    
    # Deduplicate and return requested number
    unique_results = deduplicate_results(search_results)
    return unique_results[:top_k]


def search_by_source(
    client: redis.Redis,
    query_text: str,
    source_file: str,
    top_k: int = DEFAULT_TOP_K
) -> list[SearchResult]:
    """
    Perform a filtered semantic similarity search by source file.
    
    Args:
        client: Redis client instance.
        query_text: The search query.
        source_file: Source filename to filter by.
        top_k: Number of results to return.
        
    Returns:
        list[SearchResult]: Ranked list of filtered search results.
    """
    # Generate query embedding
    query_vector = embed_query(query_text)
    query_vector_bytes = query_vector.tobytes()
    
    # Build filtered KNN query
    filter_expr = f"@source_file:{{{source_file}}}"
    base_query = f"({filter_expr})=>[KNN {top_k} @vector $query_vec AS vector_score]"
    
    q = (
        Query(base_query)
        .sort_by("vector_score")
        .return_fields("content", "source_file", "chunk_index", "metadata", "vector_score")
        .dialect(2)
    )
    
    # Execute search
    query_params = {"query_vec": query_vector_bytes}
    results = client.ft(INDEX_NAME).search(q, query_params)
    
    # Process results
    search_results = []
    for i, doc in enumerate(results.docs):
        distance = float(doc.vector_score)
        similarity = 1 - distance
        
        result = SearchResult(
            rank=i + 1,
            score=similarity,
            content=getattr(doc, "content", ""),
            source_file=getattr(doc, "source_file", "Unknown"),
            chunk_index=int(getattr(doc, "chunk_index", 0)),
            doc_id=doc.id,
            metadata=getattr(doc, "metadata", ""),
        )
        search_results.append(result)
    
    return search_results


def format_results(results: list[SearchResult], max_content_length: int = 500) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of search results.
        max_content_length: Maximum characters to show from content.
        
    Returns:
        str: Formatted results string.
    """
    if not results:
        return "No results found."
    
    lines = [f"\n{'='*60}", f"Found {len(results)} results", '='*60]
    
    for result in results:
        content_preview = result.content[:max_content_length]
        if len(result.content) > max_content_length:
            content_preview += "..."
        
        lines.extend([
            f"\n[{result.rank}] Score: {result.score:.4f}",
            f"    Source: {result.source_file} (chunk {result.chunk_index})",
            f"    Content: {content_preview}"
        ])
    
    return "\n".join(lines)
