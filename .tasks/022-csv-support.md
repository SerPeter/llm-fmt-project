# Task 022: CSV Input/Output Support

**Phase**: 4 - Extended Formats
**Priority**: -50
**Storypoints**: 3
**Status**: [x] Complete

## Objective

Add support for CSV as both an input and output format, enabling bidirectional conversion with other formats.

## Requirements

### Input (CSV Parser)
- [x] Parse CSV with header row
- [x] Support custom delimiters (comma, tab, semicolon, pipe)
- [x] Auto-detect from .csv extension
- [x] Auto-detect .tsv with tab delimiter
- [x] Handle quoted fields with commas/newlines
- [x] Support headerless mode (returns list of lists)

### Output (CSV Encoder)
- [x] Encode array of objects to CSV
- [x] Proper quoting for special characters
- [x] Handle nested values (convert to string)
- [x] Boolean/null value conversion

## Implementation

```python
class CsvParser:
    def __init__(self, *, delimiter: str = ",", has_header: bool = True) -> None:
        self.delimiter = delimiter
        self.has_header = has_header

    def parse(self, data: bytes) -> list[dict] | list[list]:
        # Returns dicts if has_header, else lists
        ...

class CsvEncoder:
    def encode(self, data: list[dict]) -> str:
        # Uses Python csv module for proper quoting
        ...
```

## CLI Usage

```bash
# CSV to JSON
llm-fmt users.csv -f json

# TSV to TOON (auto-detects tab delimiter)
llm-fmt data.tsv -f toon

# JSON array to CSV
llm-fmt users.json -f csv

# CSV to TSV
llm-fmt data.csv -f tsv
```

## Acceptance Criteria

- [x] CsvParser handles standard CSV with headers
- [x] CsvParser supports custom delimiters
- [x] CsvParser handles quoted fields correctly
- [x] CsvEncoder outputs valid CSV
- [x] CsvEncoder quotes fields with special chars
- [x] Roundtrip: CSV → JSON → CSV preserves data
- [x] All tests pass with 90%+ coverage
