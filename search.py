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
    title: str
    content: str
    source_file: str
    doc_id: str


def deduplicate_results(results: list[SearchResult]) -> list[SearchResult]:
    """
    Remove duplicate results based on title.
    
    Keeps the highest-scored result for each unique title.
    
    Args:
        results: List of search results (assumed sorted by score).
        
    Returns:
        list[SearchResult]: Deduplicated results with updated ranks.
    """
    seen_titles = set()
    unique_results = []
    
    for result in results:
        if result.title not in seen_titles:
            seen_titles.add(result.title)
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
    return_fields = return_fields or ["title", "notes", "domain", "origin", "source_file"]
    
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
            title=getattr(doc, "title", "Unknown"),
            content=getattr(doc, "notes", ""),
            source_file=getattr(doc, "source_file", "Unknown"),
            doc_id=doc.id
        )
        search_results.append(result)
    
    # Deduplicate and return requested number
    unique_results = deduplicate_results(search_results)
    return unique_results[:top_k]


def search_with_filter(
    client: redis.Redis,
    query_text: str,
    filter_field: str,
    filter_value: str,
    top_k: int = DEFAULT_TOP_K
) -> list[SearchResult]:
    """
    Perform a filtered semantic similarity search.
    
    Args:
        client: Redis client instance.
        query_text: The search query.
        filter_field: Field name to filter on (must be TagField).
        filter_value: Value to filter for.
        top_k: Number of results to return.
        
    Returns:
        list[SearchResult]: Ranked list of filtered search results.
    """
    # Generate query embedding
    query_vector = embed_query(query_text)
    query_vector_bytes = query_vector.tobytes()
    
    # Build filtered KNN query
    filter_expr = f"@{filter_field}:{{{filter_value}}}"
    base_query = f"({filter_expr})=>[KNN {top_k} @vector $query_vec AS vector_score]"
    
    q = (
        Query(base_query)
        .sort_by("vector_score")
        .return_fields("title", "notes", "domain", "origin", "source_file", "vector_score")
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
            title=getattr(doc, "title", "Unknown"),
            content=getattr(doc, "notes", ""),
            source_file=getattr(doc, "source_file", "Unknown"),
            doc_id=doc.id
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
            f"    Title: {result.title}",
            f"    Source: {result.source_file}",
            f"    Content: {content_preview}"
        ])
    
    return "\n".join(lines)
