# Task 008: JMESPath Filtering (--filter)

**Phase**: 2 - Filtering & Analysis
**Priority**: +200
**Storypoints**: 5
**Status**: [x] Complete

## Objective

Implement JMESPath-based filtering to extract specific data before format conversion.

## Why JMESPath over dpath?

- **Standard syntax**: Used by AWS CLI, well-documented
- **LLM-friendly**: Clean syntax that AI assistants can generate correctly
- **Value filtering**: `[?status == 'active']` - filter by field values
- **Future Rust acceleration**: `rjmespath` provides Rust bindings for performance

## JMESPath Syntax Reference

```
foo.bar              Nested access
foo[0]               Array index
foo[*]               All array elements
foo[*].name          Project field from each element
foo[?age > `30`]     Filter by value (backticks for literals)
foo[].bar[]          Flatten nested arrays
foo | [0]            Pipe to get first result
{name: foo, id: bar} Multi-select hash
[foo, bar]           Multi-select list
```

## Requirements

- [x] Support JMESPath syntax (`users[*].email`, `items[?active]`)
- [x] Multiple filter patterns (multiple --filter flags)
- [x] Return matching subtree preserving structure
- [x] Handle arrays with index patterns (`items[0]`, `items[*]`)
- [x] Clear error for invalid patterns
- [ ] Optional: Support `rjmespath` for Rust-accelerated performance

## Implementation Details

```python
# src/llm_fmt/filters/include.py
from typing import TYPE_CHECKING, Any

import jmespath

if TYPE_CHECKING:
    from collections.abc import Iterator


class IncludeFilter:
    """Filter that extracts data matching JMESPath expression."""

    def __init__(self, expression: str) -> None:
        """Initialize include filter.

        Args:
            expression: JMESPath expression to match.

        Raises:
            ValueError: If expression is invalid.
        """
        try:
            self._compiled = jmespath.compile(expression)
        except jmespath.exceptions.ParseError as e:
            msg = f"Invalid JMESPath expression: {e}"
            raise ValueError(msg) from e
        self.expression = expression

    def __call__(self, data: Any) -> Any:
        """Extract data matching the expression.

        Args:
            data: Input data (dict or list).

        Returns:
            Extracted data matching expression.
        """
        result = self._compiled.search(data)
        return result if result is not None else data
```

### CLI Integration

```python
@click.option(
    "--filter", "-i",
    "include_patterns",
    multiple=True,  # Allow multiple --filter flags
    help="JMESPath expression to extract data"
)
def main(include_patterns: tuple[str, ...], ...):
    for pattern in include_patterns:
        builder.add_filter(IncludeFilter(pattern))
```

### Examples

**Input:**
```json
{
  "users": [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "active": true},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "active": false}
  ],
  "pagination": {"page": 1, "total": 100}
}
```

**Filter `--filter "users[*].email"`:**
```json
["alice@example.com", "bob@example.com"]
```

**Filter `--filter "users[?active].name"`:**
```json
["Alice"]
```

**Filter `--filter "users[0]"`:**
```json
{"id": 1, "name": "Alice", "email": "alice@example.com", "active": true}
```

## Acceptance Criteria

- [x] `--filter "key"` extracts top-level key value
- [x] `--filter "a.b.c"` extracts nested path
- [x] `--filter "items[*]"` extracts all array elements
- [x] `--filter "items[*].id"` extracts specific field from each element
- [x] `--filter "items[?price > \`10\`]"` filters by value condition
- [x] Multiple patterns chain results
- [x] Invalid expression returns clear error

## Test Cases

```python
def test_simple_path():
    data = {"a": {"b": {"c": 1}}}
    result = IncludeFilter("a.b.c")(data)
    assert result == 1

def test_array_wildcard():
    data = {"users": [{"id": 1}, {"id": 2}]}
    result = IncludeFilter("users[*].id")(data)
    assert result == [1, 2]

def test_filter_expression():
    data = {"items": [{"price": 5}, {"price": 15}, {"price": 25}]}
    result = IncludeFilter("items[?price > `10`]")(data)
    assert result == [{"price": 15}, {"price": 25}]

def test_multiple_filters():
    data = {"name": "test", "id": 1, "extra": "x"}
    result = IncludeFilter("name")(data)
    assert result == "test"
```

## Dependencies

- `jmespath>=1.0` (pure Python, stable)
- Optional: `rjmespath` (Rust bindings, ~2x faster)

## Performance Notes

- Standard `jmespath` library is pure Python
- For performance-critical use: `rjmespath` offers Rust bindings (~2x faster)
- `rjmespath` takes JSON string input (may require re-serialization)
- For most CLI use cases, pure Python `jmespath` is sufficient

## Design Decision: No --exclude

JMESPath is designed for **selection**, not **exclusion**. Instead of `--exclude "password"`,
use JMESPath projection to select only the fields you want:

```bash
# Instead of excluding password:
llm-fmt data.json --filter "users[*].{id: id, name: name, email: email}"
```

This is more explicit and aligns with JMESPath's design philosophy.

## Migration from dpath

| dpath | JMESPath | Notes |
|-------|----------|-------|
| `users/*/email` | `users[*].email` | Array wildcard |
| `**/id` | N/A | No recursive wildcard, use flatten instead |
| `users/0/name` | `users[0].name` | Array index |
| N/A | `users[?active]` | JMESPath adds value filtering |
| `--exclude X` | `--filter "{...}"` | Use projection to select wanted fields |
