# Task 010: Field Exclusion (--exclude)

**Phase**: 2 - Filtering & Analysis  
**Priority**: +80
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Implement field name exclusion to remove unwanted keys from output.

## Requirements

- [ ] `--exclude "field1,field2"` removes specified fields
- [ ] Works recursively (removes at any depth)
- [ ] Pattern support for wildcards (`_*` for underscore-prefixed)
- [ ] Combine with `--filter` for compound filtering

## Implementation

```python
def exclude_fields(data: Any, patterns: list[str]) -> Any:
    """Remove fields matching patterns from data structure."""
    if isinstance(data, dict):
        return {
            k: exclude_fields(v, patterns)
            for k, v in data.items()
            if not _matches_any(k, patterns)
        }
    elif isinstance(data, list):
        return [exclude_fields(item, patterns) for item in data]
    return data

def _matches_any(key: str, patterns: list[str]) -> bool:
    """Check if key matches any exclusion pattern."""
    import fnmatch
    return any(fnmatch.fnmatch(key, p) for p in patterns)
```

## Usage

```bash
# Remove metadata fields
llm-fmt data.json --exclude "_metadata,_links,debug"

# Remove all underscore-prefixed fields
llm-fmt data.json --exclude "_*"

# Combine with filter
llm-fmt data.json --filter "users/*" --exclude "password,ssn"
```

## Acceptance Criteria

- [ ] Simple field names excluded
- [ ] Recursive exclusion works
- [ ] Wildcard patterns work
- [ ] Combines with --filter correctly
