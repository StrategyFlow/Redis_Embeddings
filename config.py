
REDIS_HOST = "ares.westpoint.edu"
#REDIS_HOST = "localhost"
REDIS_PORT = 6379


INDEX_NAME = "army_equipment_idx"
DOC_PREFIX = "doc:"



#  "all-MiniLM-L6-v2"    (384 dimensions, faster, good quality)
#  "all-mpnet-base-v2"   (768 dimensions, slower, higher quality)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

VECTOR_DIMENSIONS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
}


PDF_FILE_PATH = "Army_Equipment_Guide.pdf"


DEFAULT_TOP_K = 5  # Number of results to return by default
