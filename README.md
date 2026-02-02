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


### 1. Install Dependencies (using uv)

```bash
uv sync
```
### 2 Ingest Documents

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

### 3. Run Queries

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


