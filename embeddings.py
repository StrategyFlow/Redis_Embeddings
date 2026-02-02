"""
Embedding generation utilities.

Handles loading the embedding model and generating vector embeddings.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, VECTOR_DIMENSIONS
from models import EquipmentEntry


# Module-level cache for the model (avoid reloading)
_model_cache: dict[str, SentenceTransformer] = {}


def get_model(model_name: str | None = None) -> SentenceTransformer:
    """
    Load and cache the sentence transformer model.
    
    Args:
        model_name: Name of the model to load. Defaults to config value.
        
    Returns:
        SentenceTransformer: The loaded model.
    """
    model_name = model_name or EMBEDDING_MODEL
    
    if model_name not in _model_cache:
        print(f"  Loading model '{model_name}'...")
        _model_cache[model_name] = SentenceTransformer(model_name)
        print(f"  ✓ Model loaded")
    
    return _model_cache[model_name]


def get_vector_dimension(model_name: str | None = None) -> int:
    """
    Get the vector dimension for the specified model.
    
    Args:
        model_name: Name of the model. Defaults to config value.
        
    Returns:
        int: The dimension of vectors produced by this model.
    """
    model_name = model_name or EMBEDDING_MODEL
    
    if model_name in VECTOR_DIMENSIONS:
        return VECTOR_DIMENSIONS[model_name]
    
    # If not in our known list, load model and check
    model = get_model(model_name)
    return model.get_sentence_embedding_dimension()


def generate_embeddings(entries: list[EquipmentEntry]) -> np.ndarray:
    """
    Generate embeddings for a list of equipment entries.
    
    Uses the to_embed_text() method to get optimized text for embedding.
    
    Args:
        entries: List of EquipmentEntry objects to embed.
        
    Returns:
        np.ndarray: Array of embeddings with shape (n_entries, embedding_dim).
    """
    print(f"\n{'='*60}")
    print("STEP 2: Generating Embeddings")
    print('='*60)
    
    model = get_model()
    
    # Use the structured embed text, not raw text
    texts = [entry.to_embed_text() for entry in entries]
    
    print(f"  Embedding {len(texts)} entries...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"  ✓ Generated embeddings with shape: {embeddings.shape}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Generate an embedding for a single query string.
    
    Args:
        query: The search query text.
        
    Returns:
        np.ndarray: The query embedding vector.
    """
    model = get_model()
    embedding = model.encode(query)
    return embedding.astype(np.float32)
