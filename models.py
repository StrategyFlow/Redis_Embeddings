"""
Data models for the Army Equipment Guide.

Defines structured schemas for parsed equipment entries.
"""

from dataclasses import dataclass, field
import hashlib


@dataclass
class EquipmentEntry:
    """Represents a single equipment entry from the Army Equipment Guide."""
    
    # Core identifiers
    id: str                              # Unique ID (hash-based)
    title: str                           # Equipment name/title
    
    # Metadata fields
    weg_url: str | None = None           # WEG Location URL
    domain: list[str] = field(default_factory=list)        # Domain hierarchy
    proliferation: list[str] = field(default_factory=list) # Countries with this equipment
    origin: str | None = None            # Country of origin
    
    # Content
    notes: str = ""                      # Main descriptive text
    raw_text: str = ""                   # Original unparsed text (for debugging)
    
    # Source tracking
    source_file: str = ""                # PDF filename
    
    def content_hash(self) -> str:
        """Generate a hash of the content for deduplication."""
        content = f"{self.title}|{self.notes}".strip().lower()
        return hashlib.md5(content.encode()).hexdigest()
    
    def to_embed_text(self) -> str:
        """
        Generate the text that will be embedded.
        
        Combines relevant fields into a single string optimized for semantic search.
        """
        parts = [self.title]
        
        if self.domain:
            parts.append(f"Domain: {', '.join(self.domain)}")
        
        if self.origin:
            parts.append(f"Origin: {self.origin}")
        
        if self.proliferation:
            parts.append(f"Used by: {', '.join(self.proliferation)}")
        
        if self.notes:
            parts.append(self.notes)
        
        return ". ".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "weg_url": self.weg_url or "",
            "domain": "|".join(self.domain),  # Store as pipe-separated for Redis TagField
            "proliferation": "|".join(self.proliferation),
            "origin": self.origin or "",
            "notes": self.notes,
            "source_file": self.source_file,
        }
