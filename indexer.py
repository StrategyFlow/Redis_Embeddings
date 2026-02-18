"""
Redis vector index management.

Handles creating the search index and storing documents with embeddings.
"""

import numpy as np
import redis
from redis.commands.search.field import TextField, TagField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType

from config import INDEX_NAME, DOC_PREFIX
from embeddings import get_vector_dimension
from models import DocumentChunk


def create_index(client: redis.Redis, vector_dim: int | None = None) -> None:
    """
    Create the Redis search index for vector similarity search.
    
    Args:
        client: Redis client instance.
        vector_dim: Dimension of the vectors. Defaults to model's dimension.
    """
    vector_dim = vector_dim or get_vector_dimension()
    
    # Check if index already exists
    try:
        client.ft(INDEX_NAME).info()
        print(f"  Index '{INDEX_NAME}' already exists. Dropping and recreating...")
        client.ft(INDEX_NAME).dropindex(delete_documents=True)
    except redis.ResponseError:
        pass  # Index doesn't exist, which is fine
    
    # Define the schema for generic document chunks
    schema = (
        TextField("content"),                  # Main text content - searchable
        TagField("source_file"),               # Source filename - filterable
        TextField("chunk_index"),              # Position in document
        TextField("metadata"),                 # Flexible metadata as string
        VectorField(
            "vector",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": vector_dim,
                "DISTANCE_METRIC": "COSINE"
            }
        ),
    )
    
    # Create the index
    definition = IndexDefinition(prefix=[DOC_PREFIX], index_type=IndexType.HASH)
    client.ft(INDEX_NAME).create_index(schema, definition=definition)
    
    print(f"  ✓ Created index '{INDEX_NAME}' (vector_dim={vector_dim})")


def store_chunks(
    client: redis.Redis,
    chunks: list[DocumentChunk],
    embeddings: np.ndarray
) -> int:
    """
    Store document chunks with their embeddings in Redis.
    
    Args:
        client: Redis client instance.
        chunks: List of document chunks.
        embeddings: Array of embeddings corresponding to chunks.
        
    Returns:
        int: Number of documents stored.
    """
    print(f"\n{'='*60}")
    print("STEP 3: Storing in Redis")
    print('='*60)
    
    # Create/recreate the index
    create_index(client, vector_dim=embeddings.shape[1])
    
    print(f"  Storing {len(chunks)} chunks...")
    
    # Use pipeline for efficient batch insertion
    pipeline = client.pipeline()
    
    for i, chunk in enumerate(chunks):
        # Convert embedding to bytes
        vector_bytes = np.array(embeddings[i], dtype=np.float32).tobytes()
        
        # Get chunk data as dict and add vector
        doc_data = chunk.to_dict()
        doc_data["vector"] = vector_bytes
        
        # Add to pipeline
        doc_key = f"{DOC_PREFIX}{chunk.id}"
        pipeline.hset(doc_key, mapping=doc_data)
    
    # Execute all commands
    pipeline.execute()
    
    print(f"  ✓ Stored {len(chunks)} chunks in index '{INDEX_NAME}'")
    return len(chunks)


def get_index_info(client: redis.Redis) -> dict:
    """
    Get information about the current index.
    
    Args:
        client: Redis client instance.
        
    Returns:
        dict: Index information including document count.
    """
    try:
        info = client.ft(INDEX_NAME).info()
        return {
            "index_name": INDEX_NAME,
            "num_docs": info.get("num_docs", 0),
            "indexing": info.get("indexing", "unknown"),
        }
    except redis.ResponseError:
        return {"index_name": INDEX_NAME, "num_docs": 0, "exists": False}
