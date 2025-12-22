# Task 004: Compact JSON Output

**Phase**: 1 - MVP  
**Priority**: +100
**Storypoints**: 2  
**Status**: [ ] Not started

## Objective

Implement minified JSON output that removes all unnecessary whitespace.

## Requirements

- [ ] Output valid JSON with no whitespace
- [ ] Preserve all data exactly (lossless)
- [ ] Use orjson for fast serialization
- [ ] Option for sorted keys (deterministic output)

## Implementation Details

```python
# src/llm_fmt/formats/compact_json.py
from typing import Any
import orjson


def encode_compact_json(
    data: Any,
    sort_keys: bool = False,
) -> str:
    """
    Encode data to minified JSON.
    
    Args:
        data: Any JSON-serializable data
        sort_keys: Sort object keys alphabetically
        
    Returns:
        Minified JSON string
    """
    opts = orjson.OPT_NON_STR_KEYS
    if sort_keys:
        opts |= orjson.OPT_SORT_KEYS
    
    return orjson.dumps(data, option=opts).decode("utf-8")
```

### orjson Options Reference

```python
# Useful options for different needs
orjson.OPT_INDENT_2        # Pretty print (not for compact)
orjson.OPT_SORT_KEYS       # Deterministic key order
orjson.OPT_NON_STR_KEYS    # Allow int keys in dicts
orjson.OPT_SERIALIZE_NUMPY # Handle numpy arrays
orjson.OPT_UTC_Z           # Use 'Z' for UTC timezone
```

## Acceptance Criteria

- [ ] No whitespace in output
- [ ] Valid JSON (parseable)
- [ ] `--sort-keys` flag produces deterministic output
- [ ] Handles all JSON types (null, bool, number, string, array, object)

## Test Cases

```python
def test_compact_no_whitespace():
    data = {"key": "value", "nested": {"a": 1}}
    result = encode_compact_json(data)
    assert " " not in result
    assert "\n" not in result

def test_sorted_keys():
    data = {"z": 1, "a": 2, "m": 3}
    result = encode_compact_json(data, sort_keys=True)
    assert result == '{"a":2,"m":3,"z":1}'
```

## Token Savings

Compact JSON typically saves 10-20% tokens vs pretty-printed JSON:

| Input | Pretty JSON | Compact JSON | Savings |
|-------|-------------|--------------|---------|
| Simple object | 15 tokens | 12 tokens | 20% |
| Nested config | 234 tokens | 198 tokens | 15% |
| Array of 10 items | 156 tokens | 134 tokens | 14% |

Less dramatic than TOON, but works for any data shape.

## Notes

- Compact JSON is the safe default for non-uniform data
- Useful when TOON provides minimal benefit (nested configs)
- orjson is ~10x faster than `json.dumps(separators=(',', ':'))`
