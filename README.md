# Redis Embeddings Pipeline

Ingest any document into a Redis vector database for semantic search.

## Supported Formats

- PDF (`.pdf`)
- Text files (`.txt`)
- Markdown (`.md`)

## Quick Start

### 1. Start Local Redis

```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Ingest a Document

```bash
# Single file
uv run python ingest.py document.pdf

# Multiple files
uv run python ingest.py doc1.pdf doc2.txt doc3.md

# Preview chunks without storing
uv run python ingest.py --preview document.pdf

# Clear database and re-ingest
uv run python ingest.py --flush document.pdf
```

### 4. Query

```bash
# Single query
uv run python query.py "search terms"

# Interactive mode
uv run python query.py --interactive

# Specify number of results
uv run python query.py "search terms" --top-k 10
```

## Configuration

Edit `config.py` to:

- Toggle between local Redis and Ares server (`USE_LOCAL_REDIS`)
- Change embedding model (`EMBEDDING_MODEL`)
- Adjust chunk size (`CHUNK_SIZE`, `CHUNK_OVERLAP`)

## Project Structure

```
redis_vector_search/
├── config.py           # Settings
├── models.py           # DocumentChunk schema
├── extract_text.py     # Multi-format text extraction
├── chunker.py          # Text chunking
├── embeddings.py       # Generate embeddings
├── indexer.py          # Redis index management
├── search.py           # Vector similarity search
├── redis_client.py     # Redis connection
├── ingest.py           # Main ingestion script
├── query.py            # Query interface
├── service.py          # RAG agent interface
├── docker-compose.yaml # Local Redis
└── pyproject.toml      # Dependencies
```

## Data Flow

```
Document (PDF/TXT/MD)
       ↓
   extract_text.py    → Raw text
       ↓
   chunker.py         → Overlapping chunks
       ↓
   embeddings.py      → Vector embeddings
       ↓
   indexer.py         → Redis storage
       ↓
   search.py          → Semantic search
```

## For RAG Integration

Use `service.py` to integrate with a RAG agent:

```python
from service import search

results = search("your query", top_k=5)
for r in results:
    print(f"{r['source_file']} (chunk {r['chunk_index']}): {r['content'][:100]}...")
```

## Switching to Ares Server

Edit `config.py`:

```python
USE_LOCAL_REDIS = False  # Change from True to False
```

## Troubleshooting

### "Connection refused"
Make sure Redis is running:
```bash
docker-compose up -d
```

### "Index not found"
Run ingestion first:
```bash
uv run python ingest.py document.pdf
```

### Duplicate results
Clear and re-ingest:
```bash
uv run python ingest.py --flush document.pdf
```
