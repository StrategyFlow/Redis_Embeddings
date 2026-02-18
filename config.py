"""
Configuration settings for the embeddings pipeline.

All configurable parameters are centralized here for easy management.
"""

# =============================================================================
# Redis Connection Settings
# =============================================================================
# Toggle between local and Ares server
USE_LOCAL_REDIS = True

# Local Redis (Docker)
LOCAL_REDIS_HOST = "localhost"
LOCAL_REDIS_PORT = 6379

# Ares Redis (shared server)
ARES_REDIS_HOST = "ares.westpoint.edu"
ARES_REDIS_PORT = 6379

# Active connection (based on toggle)
REDIS_HOST = LOCAL_REDIS_HOST if USE_LOCAL_REDIS else ARES_REDIS_HOST
REDIS_PORT = LOCAL_REDIS_PORT if USE_LOCAL_REDIS else ARES_REDIS_PORT

# =============================================================================
# Index Configuration
# =============================================================================
INDEX_NAME = "embeddings_idx"
DOC_PREFIX = "doc:"

# =============================================================================
# Embedding Model Configuration
# =============================================================================
# IMPORTANT: Use the same model for both indexing and querying!
# Options:
#   - "all-MiniLM-L6-v2"    (384 dimensions, faster, good quality)
#   - "all-mpnet-base-v2"   (768 dimensions, slower, higher quality)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Vector dimensions (automatically set based on model choice)
VECTOR_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
}

# =============================================================================
# Chunking Settings
# =============================================================================
CHUNK_SIZE = 500      # words per chunk
CHUNK_OVERLAP = 50    # overlapping words between chunks

# =============================================================================
# Search Settings
# =============================================================================
DEFAULT_TOP_K = 5  # Number of results to return by default
