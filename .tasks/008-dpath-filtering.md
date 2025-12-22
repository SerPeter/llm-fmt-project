# Task 008: dpath Filtering (--filter)

**Phase**: 2 - Filtering & Analysis  
**Priority**: +200
**Storypoints**: 5  
**Status**: [ ] Not started

## Objective

Implement glob-style path filtering using dpath to extract specific data before format conversion.

## Requirements

- [ ] Support dpath glob syntax (`users/*/email`, `**/id`)
- [ ] Multiple filter patterns (comma-separated or multiple flags)
- [ ] Return matching subtree, not just values
- [ ] Handle arrays with index patterns (`items/0`, `items/*`)
- [ ] Clear error for invalid patterns

## dpath Syntax Reference

```
path/to/key          Exact path
path/*/key           Wildcard single level
path/**/key          Recursive wildcard (any depth)
path/[0]/key         Array index
path/[0:5]/key       Array slice
path/*/[id=123]      Filter by value (custom extension)
```

## Implementation Details

```python
# src/llm_fmt/filter.py
from __future__ import annotations

from typing import Any
import dpath.util


def filter_by_path(data: Any, patterns: list[str]) -> Any:
    """
    Filter data to only matching paths.
    
    Args:
        data: Input data structure
        patterns: List of dpath glob patterns
        
    Returns:
        Filtered data structure preserving hierarchy
    """
    if not patterns:
        return data
    
    result = {}
    
    for pattern in patterns:
        try:
            # Get all matching paths and values
            for path, value in dpath.util.search(data, pattern, yielded=True):
                # Merge into result, preserving structure
                dpath.util.new(result, path, value)
        except KeyError:
            # Pattern matched nothing - that's okay
            pass
    
    return result if result else data


def filter_by_paths_extract(data: Any, patterns: list[str]) -> list[Any]:
    """
    Extract just the values matching patterns (flat list).
    
    Useful for: "give me all emails from this response"
    """
    results = []
    for pattern in patterns:
        results.extend(dpath.util.values(data, pattern))
    return results
```

### CLI Integration

```python
@click.option(
    "--filter",
    "filter_patterns",
    multiple=True,  # Allow multiple --filter flags
    help="dpath glob pattern(s) to include"
)
def main(filter_patterns: tuple[str, ...], ...):
    if filter_patterns:
        data = filter_by_path(data, list(filter_patterns))
```

### Examples

**Input:**
```json
{
  "users": [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "metadata": {...}},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "metadata": {...}}
  ],
  "pagination": {"page": 1, "total": 100}
}
```

**Filter `--filter "users/*/email,name"`:**
```json
{
  "users": [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
  ]
}
```

**Filter `--filter "users/*/email"` (extract mode):**
```
["alice@example.com", "bob@example.com"]
```

## Acceptance Criteria

- [ ] `--filter "key"` extracts top-level key
- [ ] `--filter "a/b/c"` extracts nested path
- [ ] `--filter "items/*"` extracts all array elements
- [ ] `--filter "items/*/id"` extracts specific field from each element
- [ ] `--filter "**/id"` finds all `id` fields at any depth
- [ ] Multiple patterns combine results
- [ ] Non-matching pattern returns empty (not error)

## Test Cases

```python
def test_simple_path():
    data = {"a": {"b": {"c": 1}}}
    result = filter_by_path(data, ["a/b/c"])
    assert result == {"a": {"b": {"c": 1}}}

def test_wildcard():
    data = {"users": [{"id": 1}, {"id": 2}]}
    result = filter_by_path(data, ["users/*/id"])
    assert result == {"users": [{"id": 1}, {"id": 2}]}

def test_recursive_wildcard():
    data = {"a": {"id": 1, "b": {"id": 2}}}
    values = filter_by_paths_extract(data, ["**/id"])
    assert values == [1, 2]

def test_multiple_patterns():
    data = {"name": "test", "id": 1, "extra": "x"}
    result = filter_by_path(data, ["name", "id"])
    assert result == {"name": "test", "id": 1}
```

## Dependencies

- `dpath>=2.2`

## Notes

- dpath is pure Python - consider Rust alternative for large data
- `dpath.util.search()` with `yielded=True` is memory efficient
- Glob patterns are case-sensitive
- Consider adding `--filter-mode extract` for flat value list output
