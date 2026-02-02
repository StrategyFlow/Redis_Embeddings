"""Debug script to examine PDF structure. Thx to Claude"""
import fitz

pdf_path = "Army_Equipment_Guide.pdf"

# Extract text
with fitz.open(pdf_path) as doc:
    full_text = ""
    for page in doc:
        full_text += page.get_text()

# Show first 5000 characters
print("=" * 60)
print("FIRST 5000 CHARACTERS OF PDF")
print("=" * 60)
print(full_text[:5000])

print("\n" + "=" * 60)
print("SEARCHING FOR PATTERNS")
print("=" * 60)

# Check what patterns exist
patterns_to_find = [
    "WEG Location:",
    "Tiers:",
    "Domain:",
    "Proliferation:",
    "Origin:",
    "Notes",
    "Notes:",
]

for pattern in patterns_to_find:
    count = full_text.count(pattern)
    print(f"'{pattern}' appears {count} times")

# Show a few raw entries split by current pattern
print("\n" + "=" * 60)
print("SAMPLE RAW ENTRY (split on 'WEG Location')")
print("=" * 60)
import re
entries = re.split(r'(?=\nWEG Location:\s*https?://)', full_text)
print(f"Found {len(entries)} entries with this split")
if len(entries) > 1:
    print("\n--- Entry 1 (first 1500 chars) ---")
    print(entries[1][:1500])