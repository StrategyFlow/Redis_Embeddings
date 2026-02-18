"""
Data models for the embeddings pipeline.

Defines generic document chunk schema for any document type.
"""

from dataclasses import dataclass, field
import hashlib


@dataclass
class DocumentChunk:
    """Represents a chunk of text from any document."""
    
    # Core identifiers
    id: str                              # Unique ID (hash-based)
    content: str                         # The actual text content
    
    # Source tracking
    source_file: str                     # Original filename
    chunk_index: int                     # Position in document (0, 1, 2, ...)
    
    # Flexible metadata
    metadata: dict = field(default_factory=dict)  # title, author, date, etc.
    
    def content_hash(self) -> str:
        """Generate a hash of the content for deduplication."""
        return hashlib.md5(self.content.strip().lower().encode()).hexdigest()
    
    def to_embed_text(self) -> str:
        """
        Generate the text that will be embedded.
        
        Returns the content, optionally prefixed with metadata.
        """
        parts = []
        
        # Add title if present
        if self.metadata.get("title"):
            parts.append(self.metadata["title"])
        
        # Add main content
        parts.append(self.content)
        
        return ". ".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "id": self.id,
            "content": self.content,
            "source_file": self.source_file,
            "chunk_index": str(self.chunk_index),
            "metadata": str(self.metadata),  # Store as string for Redis
        }
    
    @classmethod
    def create(cls, content: str, source_file: str, chunk_index: int, metadata: dict = None) -> "DocumentChunk":
        """Factory method to create a DocumentChunk with auto-generated ID."""
        chunk = cls(
            id="",
            content=content,
            source_file=source_file,
            chunk_index=chunk_index,
            metadata=metadata or {},
        )
        # Generate ID from source file and content hash
        chunk.id = f"{source_file}_{chunk_index}_{chunk.content_hash()[:8]}"
        return chunk
