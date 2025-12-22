# Task 003: TOON Output Format

**Phase**: 1 - MVP  
**Priority**: +300
**Storypoints**: 5  
**Status**: [ ] Not started

## Objective

Implement TOON (Token-Oriented Object Notation) encoding for maximum token efficiency on uniform arrays.

## Requirements

- [ ] Encode Python dicts/lists to TOON format
- [ ] Support tabular array syntax `[N]{fields}:`
- [ ] Handle nested structures with indentation
- [ ] Escape special characters in values
- [ ] Round-trip compatibility with toon-format spec

## TOON Format Reference

### Basic Syntax

```
# Object
{name,age}:
  Alice,30

# Array of objects (tabular - key optimization)
users[2]{id,name,role}:
  1,Alice,admin
  2,Bob,user

# Nested
config{database}:
  database{host,port}:
    localhost,5432

# Mixed types
items[3]:
  string value
  42
  true
```

### Key Rules

1. Arrays with uniform objects use `[N]{field1,field2}:` header
2. Fields declared once, values on subsequent lines
3. Values separated by commas
4. Strings containing `,` or newlines must be quoted
5. Indentation indicates nesting (2 spaces)

## Implementation Details

### Encoder Module

```python
# src/llm_fmt/formats/toon.py
from __future__ import annotations

from typing import Any


def encode_toon(data: Any, indent: int = 0) -> str:
    """
    Encode Python data to TOON format.
    
    Args:
        data: Dict, list, or primitive value
        indent: Current indentation level
        
    Returns:
        TOON-formatted string
    """
    if isinstance(data, dict):
        return _encode_object(data, indent)
    elif isinstance(data, list):
        return _encode_array(data, indent)
    else:
        return _encode_value(data)


def _encode_object(obj: dict, indent: int) -> str:
    """Encode a dictionary."""
    if not obj:
        return "{}"
    
    prefix = "  " * indent
    fields = ",".join(obj.keys())
    lines = [f"{{{fields}}}:"]
    
    for key, value in obj.items():
        if isinstance(value, (dict, list)):
            lines.append(f"{prefix}  {key}:")
            lines.append(_encode_nested(value, indent + 2))
        else:
            lines.append(f"{prefix}  {_encode_value(value)}")
    
    return "\n".join(lines)


def _encode_array(arr: list, indent: int) -> str:
    """Encode a list, using tabular format if uniform."""
    if not arr:
        return "[]"
    
    if _is_uniform_object_array(arr):
        return _encode_tabular(arr, indent)
    else:
        return _encode_simple_array(arr, indent)


def _is_uniform_object_array(arr: list) -> bool:
    """Check if array contains objects with identical keys."""
    if not arr or not isinstance(arr[0], dict):
        return False
    
    keys = set(arr[0].keys())
    return all(
        isinstance(item, dict) and set(item.keys()) == keys
        for item in arr
    )


def _encode_tabular(arr: list[dict], indent: int) -> str:
    """Encode uniform object array in tabular format."""
    prefix = "  " * indent
    fields = list(arr[0].keys())
    header = f"[{len(arr)}]{{{','.join(fields)}}}:"
    
    lines = [header]
    for item in arr:
        values = [_encode_value(item[f]) for f in fields]
        lines.append(f"{prefix}  {','.join(values)}")
    
    return "\n".join(lines)


def _encode_value(value: Any) -> str:
    """Encode a primitive value."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        if "," in value or "\n" in value or value.startswith('"'):
            return f'"{value}"'  # TODO: proper escaping
        return value
    else:
        return str(value)
```

### Integration with toon-format library

Consider using the official `toon-format` package as reference or wrapper:

```python
try:
    import toon_format
    def encode_toon(data: Any) -> str:
        return toon_format.encode(data)
except ImportError:
    # Fall back to built-in implementation
    pass
```

## Acceptance Criteria

- [ ] Simple objects encode correctly
- [ ] Uniform arrays use tabular syntax
- [ ] Nested structures maintain proper indentation
- [ ] Special characters are escaped
- [ ] Output matches toon-format spec examples
- [ ] Token count is lower than equivalent JSON

## Test Cases

```python
def test_simple_object():
    data = {"name": "Alice", "age": 30}
    result = encode_toon(data)
    assert "{name,age}:" in result
    assert "Alice,30" in result

def test_uniform_array():
    data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    result = encode_toon(data)
    assert "[2]{id,name}:" in result

def test_nested():
    ...

def test_escaping():
    data = {"msg": "Hello, World"}
    result = encode_toon(data)
    assert '"Hello, World"' in result
```

## Dependencies

- Optional: `toon-format` (for reference implementation)

## Notes

- TOON v2.0 spec: https://toonformat.dev
- Tabular format saves 30-60% tokens on uniform arrays
- Non-uniform arrays fall back to simple list format
- Consider streaming output for very large arrays
