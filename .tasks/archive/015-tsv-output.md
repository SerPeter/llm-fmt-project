# Task 015: TSV Output Format

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +50
**Storypoints**: 3  
**Status**: [x] Complete

## Objective

Implement TSV (tab-separated values) output for flat tabular data.

## Requirements

- [x] Convert uniform arrays to TSV
- [x] Header row with field names
- [x] Tab-separated values (better token efficiency than CSV)
- [x] Escape tabs and newlines in values
- [x] Error for non-tabular data

## Why TSV over CSV

Tabs tokenize more efficiently than commas in most BPE vocabularies:
- Tab: usually 1 token
- Comma + space: often 2 tokens

TSV achieves 40-50% token savings on flat tabular data.

## Implementation

```python
def encode_tsv(data: list[dict]) -> str:
    """Encode uniform array as TSV."""
    if not data or not isinstance(data[0], dict):
        raise ValueError("TSV requires uniform array of objects")
    
    headers = list(data[0].keys())
    lines = ["\t".join(headers)]
    
    for item in data:
        values = [_escape_tsv(str(item.get(h, ""))) for h in headers]
        lines.append("\t".join(values))
    
    return "\n".join(lines)

def _escape_tsv(value: str) -> str:
    """Escape tabs and newlines."""
    return value.replace("\t", "\\t").replace("\n", "\\n")
```

## Acceptance Criteria

- [x] Uniform arrays convert to TSV
- [x] Headers included
- [x] Special characters escaped
- [x] Clear error for non-tabular data
