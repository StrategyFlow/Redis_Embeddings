# Redis Vector Search

So far this is only configured to use the Army Equipment Guide for embeddings, but it can be expanded pretty easily to take in more when we get to that step of the project.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PDF Document  │────▶│  Text Extraction │────▶│    Chunking     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Redis Vector   │◀────│  Store Vectors   │◀────│   Embeddings    │
│     Index       │     │   + Metadata     │     │   Generation    │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Query     │────▶│  Embed Query     │────▶│   KNN Search    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Project Structure

```
redis_vector_search/
├── pyproject.toml      # Project config & dependencies (for uv)
├── config.py           # All configuration settings
├── redis_client.py     # Redis connection utilities
├── pdf_processor.py    # PDF text extraction and chunking
├── embeddings.py       # Embedding model and generation
├── indexer.py          # Redis index management
├── search.py           # Query and search functionality
├── ingest.py           # Main ingestion script
├── query.py            # Main query script
├── docker-compose.yaml # Redis Stack container
└── README.md           # This file
```

## Quick Start

### 1. Start Redis

```bash
docker-compose up -d
```

Verify it's running:
```bash
docker-compose ps
```

### 2. Install Dependencies (using uv)

```bash
# Install uv if you haven't already
# See: https://docs.astral.sh/uv/getting-started/installation/

# Sync dependencies (creates .venv automatically)
uv sync
```

That's it! `uv sync` reads `pyproject.toml`, creates a virtual environment, and installs all dependencies.

### 3. Ingest Documents

Place your PDF file in the project directory (or update `PDF_FILE_PATH` in `config.py`), then run:

```bash
uv run python ingest.py
```

Or specify a different PDF:
```bash
uv run python ingest.py path/to/document.pdf
```

To clear existing data first:
```bash
uv run python ingest.py --flush
```

### 4. Run Queries

Single query:
```bash
uv run python query.py "Chinese Military Helicopters"
```

With custom result count:
```bash
uv run python query.py "electronic warfare systems" --top-k 10
```

Interactive mode:
```bash
uv run python query.py --interactive
```

> **Note:** `uv run` automatically uses the project's virtual environment. You don't need to activate it manually.

## Configuration

All settings are in `config.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `INDEX_NAME` | Name of the search index | `army_equipment_idx` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `DEFAULT_TOP_K` | Default number of results | `5` |

### Embedding Models

Two models are pre-configured:

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good |
| `all-mpnet-base-v2` | 768 | Slower | Higher |

**Important**: Use the same model for both ingestion and queries!

## Usage Examples

### Python API

```python
from redis_client import get_redis_client
from search import search, format_results

# Connect
client = get_redis_client()

# Search
results = search(client, "reconnaissance drones", top_k=5)

# Display
print(format_results(results))

# Or work with results directly
for result in results:
    print(f"{result.rank}. {result.title} (score: {result.score:.3f})")
```

### Filtered Search

```python
from search import search_with_filter

# Search only in specific source files
results = search_with_filter(
    client,
    query_text="helicopters",
    filter_field="source_file",
    filter_value="Army_Equipment_Guide.pdf",
    top_k=5
)
```

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Start Redis | `docker-compose up -d` |
| Stop Redis | `docker-compose down` |
| View Redis logs | `docker-compose logs -f` |
| Ingest PDF | `uv run python ingest.py` |
| Ingest + clear old data | `uv run python ingest.py --flush` |
| Single query | `uv run python query.py "search terms"` |
| Query with more results | `uv run python query.py "search terms" --top-k 10` |
| Interactive queries | `uv run python query.py --interactive` |


### Adding New Document Types

1. Create a new processor in `pdf_processor.py` or a new module
2. Return `list[DocumentChunk]` from your processor
3. Use existing `generate_embeddings()` and `store_documents()` functions


