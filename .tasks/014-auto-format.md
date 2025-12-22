# Task 014: Auto Format Selection

**Phase**: 3 - Auto-Selection & Polish  
**Priority**: +120
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Implement intelligent format auto-selection based on data shape analysis.

## Requirements

- [ ] `--format auto` (or default) picks optimal format
- [ ] Detection of uniform arrays → TOON
- [ ] Detection of flat configs → YAML
- [ ] Fallback to compact JSON for complex structures
- [ ] Fast detection (don't scan entire dataset)

## Decision Logic

```
Is root a list?
├─ Yes → Are all items dicts with same keys?
│        ├─ Yes → TOON (30-60% savings)
│        └─ No  → Is it flat primitives?
│                 ├─ Yes → TSV (40-50% savings)
│                 └─ No  → Compact JSON
└─ No (root is dict) → What's the max depth?
                       ├─ Shallow (≤2) → YAML (20-40% savings)
                       └─ Deep (>2) → Compact JSON
```

## Implementation Details

```python
# src/llm_fmt/detection.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DataShape:
    """Analysis of data structure shape."""
    root_type: str  # "object", "array", "primitive"
    is_uniform_array: bool
    array_length: int | None
    field_count: int | None
    max_depth: int
    is_mostly_primitives: bool
    sample_keys: list[str]


def detect_data_shape(data: Any, max_sample: int = 100) -> DataShape:
    """
    Analyze data structure to determine optimal format.
    
    Args:
        data: Input data
        max_sample: Max items to sample from arrays
        
    Returns:
        DataShape analysis
    """
    if isinstance(data, list):
        return _analyze_array(data, max_sample)
    elif isinstance(data, dict):
        return _analyze_object(data)
    else:
        return DataShape(
            root_type="primitive",
            is_uniform_array=False,
            array_length=None,
            field_count=None,
            max_depth=0,
            is_mostly_primitives=True,
            sample_keys=[],
        )


def _analyze_array(arr: list, max_sample: int) -> DataShape:
    """Analyze array structure."""
    if not arr:
        return DataShape("array", False, 0, None, 1, True, [])
    
    # Sample for large arrays
    sample = arr[:max_sample] if len(arr) > max_sample else arr
    
    # Check uniformity
    if all(isinstance(item, dict) for item in sample):
        keys_set = set(sample[0].keys())
        is_uniform = all(set(item.keys()) == keys_set for item in sample)
        
        if is_uniform:
            max_depth = _calculate_depth(sample[0])
            return DataShape(
                root_type="array",
                is_uniform_array=True,
                array_length=len(arr),
                field_count=len(keys_set),
                max_depth=max_depth + 1,
                is_mostly_primitives=_is_mostly_primitives(sample[0]),
                sample_keys=list(keys_set)[:10],
            )
    
    # Non-uniform array
    max_depth = max(_calculate_depth(item) for item in sample)
    return DataShape(
        root_type="array",
        is_uniform_array=False,
        array_length=len(arr),
        field_count=None,
        max_depth=max_depth + 1,
        is_mostly_primitives=all(_is_primitive(item) for item in sample),
        sample_keys=[],
    )


def _calculate_depth(data: Any, current: int = 0) -> int:
    """Calculate maximum nesting depth."""
    if isinstance(data, dict):
        if not data:
            return current
        return max(_calculate_depth(v, current + 1) for v in data.values())
    elif isinstance(data, list):
        if not data:
            return current
        return max(_calculate_depth(item, current + 1) for item in data)
    return current


def _is_primitive(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool, type(None)))


def _is_mostly_primitives(obj: dict) -> bool:
    """Check if object values are mostly primitives."""
    if not obj:
        return True
    primitives = sum(1 for v in obj.values() if _is_primitive(v))
    return primitives / len(obj) > 0.7


# Format selector
def select_format(data: Any) -> str:
    """Select optimal format for data."""
    shape = detect_data_shape(data)
    
    if shape.is_uniform_array and shape.array_length and shape.array_length > 1:
        return "toon"
    
    if shape.root_type == "array" and shape.is_mostly_primitives:
        return "tsv"
    
    if shape.max_depth <= 2:
        return "yaml"
    
    return "compact-json"
```

### CLI Integration

```python
@click.option(
    "-f", "--format",
    type=click.Choice(["toon", "compact-json", "yaml", "tsv", "auto"]),
    default="auto",
    help="Output format (default: auto)"
)
def main(format: str, ...):
    if format == "auto":
        format = select_format(data)
        if verbose:
            click.echo(f"Auto-selected: {format}", err=True)
```

## Acceptance Criteria

- [ ] Uniform array → TOON automatically
- [ ] Shallow dict → YAML automatically
- [ ] Deep nested → compact-json automatically
- [ ] Large arrays sampled efficiently (not full scan)
- [ ] `--verbose` shows which format was selected

## Test Cases

```python
def test_auto_uniform_array():
    data = [{"id": 1}, {"id": 2}]
    assert select_format(data) == "toon"

def test_auto_shallow_dict():
    data = {"name": "test", "value": 123}
    assert select_format(data) == "yaml"

def test_auto_deep_nested():
    data = {"a": {"b": {"c": {"d": 1}}}}
    assert select_format(data) == "compact-json"

def test_auto_primitive_array():
    data = [1, 2, 3, 4, 5]
    assert select_format(data) == "tsv"
```

## Notes

- Sampling prevents O(n) scan on large arrays
- Could add heuristics for specific patterns (e.g., API responses)
- Consider user preferences from config file
- May want `--format auto --prefer toon` to hint preference
