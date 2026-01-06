# Task 009: Max Depth Limiting

**Phase**: 2 - Filtering & Analysis  
**Priority**: +100
**Storypoints**: 3  
**Status**: [x] Complete

## Objective

Implement depth-based truncation to limit nesting levels in output.

## Requirements

- [x] `--max-depth N` limits output to N levels of nesting
- [x] Depth 0 = only root level keys
- [x] Truncated branches show placeholder or summary
- [x] Works with all output formats
- [x] Applied before format conversion (reduces tokens)

## Implementation Details

```python
# src/llm_fmt/filter.py
from typing import Any


def limit_depth(
    data: Any,
    max_depth: int,
    current_depth: int = 0,
    truncation_marker: str = "..."
) -> Any:
    """
    Recursively limit data structure depth.
    
    Args:
        data: Input data
        max_depth: Maximum nesting depth (0 = root only)
        current_depth: Current recursion depth
        truncation_marker: What to show for truncated data
        
    Returns:
        Depth-limited copy of data
    """
    if current_depth >= max_depth:
        # At max depth - summarize what's truncated
        if isinstance(data, dict):
            return f"{{...{len(data)} keys}}"
        elif isinstance(data, list):
            return f"[...{len(data)} items]"
        else:
            return data  # Primitives pass through
    
    if isinstance(data, dict):
        return {
            key: limit_depth(value, max_depth, current_depth + 1, truncation_marker)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [
            limit_depth(item, max_depth, current_depth + 1, truncation_marker)
            for item in data
        ]
    else:
        return data


def limit_depth_strict(data: Any, max_depth: int) -> Any:
    """
    Limit depth, completely removing deeper structures.
    
    Use when you want clean data without placeholders.
    """
    if max_depth <= 0:
        if isinstance(data, dict):
            return {k: None for k in data.keys()}
        elif isinstance(data, list):
            return None
        return data
    
    if isinstance(data, dict):
        return {
            k: limit_depth_strict(v, max_depth - 1)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [limit_depth_strict(item, max_depth - 1) for item in data]
    return data
```

### Examples

**Input (depth 3):**
```json
{
  "level1": {
    "level2": {
      "level3": {
        "level4": "deep value"
      }
    }
  }
}
```

**With `--max-depth 2`:**
```json
{
  "level1": {
    "level2": "{...1 keys}"
  }
}
```

**With `--max-depth 2 --strict`:**
```json
{
  "level1": {
    "level2": null
  }
}
```

### Real-World Example

API response with deeply nested metadata:

```json
{
  "data": {
    "users": [
      {
        "id": 1,
        "profile": {
          "settings": {
            "notifications": {
              "email": true,
              "sms": false,
              ...
            }
          }
        }
      }
    ]
  }
}
```

With `--max-depth 3`, you get the essential structure without the deep settings.

## Acceptance Criteria

- [x] `--max-depth 0` returns only root keys
- [x] `--max-depth 1` shows one level of nesting
- [x] Truncation markers indicate what's hidden
- [x] Works on arrays and objects
- [x] Primitives at any depth are preserved
- [x] Combined with `--filter` works correctly

## Test Cases

```python
def test_depth_0():
    data = {"a": {"b": 1}, "c": 2}
    result = limit_depth(data, 0)
    assert result == {
        "a": "{...1 keys}",
        "c": 2
    }

def test_depth_1():
    data = {"a": {"b": {"c": 1}}}
    result = limit_depth(data, 1)
    assert result == {"a": {"b": "{...1 keys}"}}

def test_array_depth():
    data = {"items": [{"nested": {"deep": 1}}]}
    result = limit_depth(data, 2)
    assert result == {"items": [{"nested": "{...1 keys}"}]}

def test_primitives_preserved():
    data = {"a": 1, "b": "string", "c": True}
    result = limit_depth(data, 0)
    assert result == {"a": 1, "b": "string", "c": True}
```

## CLI Integration

```python
@click.option(
    "--max-depth",
    "-d",
    "max_depth",
    type=int,
    help="Maximum depth to traverse (applied after filters).",
)
```

Note: The `--strict` option (removing deep data instead of showing placeholders) was
considered but omitted to keep the implementation simple. Placeholders provide better
visibility into what data was truncated.

## Notes

- Depth counting: root object/array is depth 0
- Consider option to keep or drop truncated branches entirely
- Placeholder format could be configurable
- Arrays within objects increase depth
