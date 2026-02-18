"""
Embeddings service interface.
Provides search functionality for the RAG agent.
"""

from redis_client import get_redis_client
from search import search_documents
from embeddings import load_model, generate_embedding


class EmbeddingsService:
    def __init__(self):
        self.client = get_redis_client()
        self.model = load_model()
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of {content, title, score, source}
        """
        results = search_documents(self.client, query, top_k)
        return [
            {
                "content": r.get("notes", ""),
                "title": r.get("title", ""),
                "score": r.get("score", 0.0),
                "source": r.get("source_file", ""),
                "domain": r.get("domain", ""),
                "origin": r.get("origin", ""),
            }
            for r in results
        ]


# Singleton instance
_service = None


def get_service() -> EmbeddingsService:
    """Get or create the embeddings service instance."""
    global _service
    if _service is None:
        _service = EmbeddingsService()
    return _service


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Convenience function for simple usage.
    
    Example:
        from service import search
        results = search("Chinese helicopters", top_k=5)
    """
    return get_service().search(query, top_k)