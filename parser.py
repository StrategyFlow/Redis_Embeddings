"""
Parser for Army Equipment Guide PDF.

Extracts structured equipment entries from raw PDF text.
"""

import re
from models import EquipmentEntry


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        str: Concatenated text from all pages.
    """
    import fitz  # PyMuPDF - import as fitz
    
    print(f"  Extracting text from '{pdf_path}'...")
    
    full_text = ""
    with fitz.open(pdf_path) as doc:
        page_count = len(doc)
        for page in doc:
            full_text += page.get_text()
    
    print(f"Extracted text from {page_count} pages ({len(full_text):,} characters)")
    return full_text


def split_into_raw_entries(full_text: str) -> list[str]:
    """
    Split the full PDF text into individual raw entry blocks.
    
    Each entry starts with a title line followed by 'WEG Location:'.
    
    Args:
        full_text: Complete extracted text from PDF.
        
    Returns:
        list[str]: List of raw text blocks, one per entry.
    """
    # Split on WEG Location pattern
    # We need to capture the title which appears BEFORE WEG Location
    # So we split and then prepend the title from the previous chunk
    
    # First, split keeping the title with each entry
    # Pattern: split right before a line that starts with title text followed by WEG Location
    pattern = r'(?=\nWEG Location:\s*https?://)'
    
    raw_entries = re.split(pattern, full_text)
    
    # Filter out empty entries
    raw_entries = [entry.strip() for entry in raw_entries if entry.strip()]
    
    return raw_entries


def parse_entry(raw_text: str, source_file: str = "") -> EquipmentEntry | None:
    """
    Parse a single raw text block into a structured EquipmentEntry.
    
    Expected format:
        WEG Location: https://...
        Tiers:
        Domain: Air, Something, Something Else
        Proliferation: Country1, Country2
        Origin: Country
        Notes
        Actual content here...
    
    Note: Title appears BEFORE this block (handled separately)
    
    Args:
        raw_text: Raw text for one equipment entry.
        source_file: Name of the source PDF file.
        
    Returns:
        EquipmentEntry if parsing succeeds, None if entry is invalid.
    """
    # Extract WEG URL
    weg_match = re.search(r'WEG Location:\s*(https?://\S+)', raw_text)
    weg_url = weg_match.group(1).strip() if weg_match else None
    
    # Extract Domain (everything after "Domain:" until next field line)
    domain_match = re.search(r'Domain:\s*(.+?)(?=\nProliferation:|\nOrigin:|\nNotes)', raw_text, re.DOTALL)
    domain = []
    if domain_match:
        domain_text = domain_match.group(1).strip().replace('\n', ' ')
        domain = [d.strip() for d in domain_text.split(',') if d.strip()]
    
    # Extract Proliferation
    prolif_match = re.search(r'Proliferation:\s*(.+?)(?=\nOrigin:|\nNotes)', raw_text, re.DOTALL)
    proliferation = []
    if prolif_match:
        prolif_text = prolif_match.group(1).strip().replace('\n', ' ')
        proliferation = [p.strip() for p in prolif_text.split(',') if p.strip()]
    
    # Extract Origin
    origin_match = re.search(r'Origin:\s*(.+?)(?=\nNotes)', raw_text, re.DOTALL)
    origin = origin_match.group(1).strip().replace('\n', ' ') if origin_match else None
    
    # Extract Notes - everything after "Notes" line until end or next entry marker
    # Also remove footer text like "For Training Use Only" and page numbers
    notes_match = re.search(r'\nNotes\n(.*)', raw_text, re.DOTALL)
    notes = ""
    if notes_match:
        notes = notes_match.group(1).strip()
        # Remove common footer patterns
        notes = re.sub(r'For Training Use Only.*?(?=\n|$)', '', notes)
        notes = re.sub(r'Exported \(UTC\).*?(?=\n|$)', '', notes)
        notes = ' '.join(notes.split())  # Normalize whitespace
    
    # Extract title from Notes content - it's typically the first phrase before "This is" or "The"
    # Or use the first sentence/phrase of the notes
    title = ""
    if notes:
        # Try to get title from start of notes - often format is "Name This is a..."
        # Look for pattern like "ABC-123 This is" or "Name The system"
        title_match = re.match(r'^([\w\-\d\s\(\)]+?)(?:\s+This\s+|\s+The\s+|\s+is\s+|\s+are\s+)', notes)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback: use first few words
            words = notes.split()[:6]
            title = ' '.join(words)
    
    # Skip if no meaningful content
    if not notes or len(notes) < 20:
        return None
    
    # Create entry
    entry = EquipmentEntry(
        id="",  # Will be set after hashing
        title=title if title else "Unknown",
        weg_url=weg_url,
        domain=domain,
        proliferation=proliferation,
        origin=origin,
        notes=notes,
        raw_text=raw_text,
        source_file=source_file,
    )
    
    # Generate ID from content hash
    entry.id = f"{source_file}_{entry.content_hash()[:12]}"
    
    return entry


def parse_pdf(pdf_path: str) -> list[EquipmentEntry]:
    """
    Complete pipeline to parse a PDF into structured equipment entries.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        list[EquipmentEntry]: List of parsed equipment entries.
    """
    print(f"\n{'='*60}")
    print("STEP 1: Extracting and Parsing PDF")
    print('='*60)
    
    # Extract text
    full_text = extract_text_from_pdf(pdf_path)
    
    # Split into raw entries
    print("Splitting into entries...")
    raw_entries = split_into_raw_entries(full_text)
    print(f"Found {len(raw_entries)} raw entries")
    
    # Parse each entry
    print("  Parsing entries...")
    entries = []
    failed_count = 0
    
    for raw_text in raw_entries:
        entry = parse_entry(raw_text, source_file=pdf_path)
        if entry:
            entries.append(entry)
        else:
            failed_count += 1
    
    print(f"Successfully parsed {len(entries)} entries")
    if failed_count > 0:
        print(f"Failed to parse {failed_count} entries")
    
    # Deduplicate
    print("Deduplicating...")
    entries = deduplicate_entries(entries)
    print(f" {len(entries)} unique entries after deduplication")
    
    return entries


def deduplicate_entries(entries: list[EquipmentEntry]) -> list[EquipmentEntry]:
    """
    Remove duplicate entries based on content hash.
    
    Args:
        entries: List of parsed entries.
        
    Returns:
        list[EquipmentEntry]: Deduplicated list.
    """
    seen_hashes = set()
    unique_entries = []
    
    for entry in entries:
        content_hash = entry.content_hash()
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_entries.append(entry)
    
    return unique_entries


# Debug utilities

def preview_entries(entries: list[EquipmentEntry], count: int = 5) -> None:
    """Print a preview of parsed entries for verification."""
    print(f"\n{'='*60}")
    print(f"PREVIEW: First {count} entries")
    print('='*60)
    
    for i, entry in enumerate(entries[:count]):
        print(f"\n--- Entry {i+1} ---")
        print(f"Title: {entry.title}")
        print(f"WEG URL: {entry.weg_url}")
        print(f"Domain: {entry.domain}")
        print(f"Proliferation: {entry.proliferation}")
        print(f"Origin: {entry.origin}")
        print(f"Notes: {entry.notes[:200]}..." if len(entry.notes) > 200 else f"Notes: {entry.notes}")
        print(f"Embed text preview: {entry.to_embed_text()[:300]}...")