# Task 022: Truncation Strategies

**Phase**: 4 - Performance & Extensions
**Priority**: +90
**Storypoints**: 8
**Status**: [ ] Not started

## Objective

Implement intelligent, token-aware truncation strategies to fit large datasets within LLM context windows while preserving the most relevant information.

## Requirements

- [ ] `--max-tokens N` truncates output to fit token budget
- [ ] `--max-items N` limits array lengths (horizontal truncation)
- [ ] `--max-string-length N` truncates long string values
- [ ] Multiple truncation strategies (head, tail, sample, balanced)
- [ ] `--preserve` option to protect important fields from truncation
- [ ] Smart summaries showing what was truncated
- [ ] Works with all output formats

## Implementation Details

```python
# src/llm_fmt/truncate.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
import random

from llm_fmt.tokens import count_tokens, estimate_tokens


class TruncationStrategy(Enum):
    HEAD = "head"      # Keep first N items
    TAIL = "tail"      # Keep last N items
    SAMPLE = "sample"  # Random sample
    BALANCED = "balanced"  # Keep some from start and end


@dataclass
class TruncationConfig:
    max_tokens: int | None = None
    max_items: int | None = None
    max_string_length: int | None = None
    strategy: TruncationStrategy = TruncationStrategy.HEAD
    preserve_paths: list[str] | None = None
    show_summary: bool = True


@dataclass
class TruncationResult:
    data: Any
    original_tokens: int
    final_tokens: int
    truncated: bool
    summary: TruncationSummary | None = None


@dataclass
class TruncationSummary:
    arrays_truncated: int
    items_removed: int
    strings_truncated: int
    chars_removed: int


def truncate_array(
    arr: list,
    max_items: int,
    strategy: TruncationStrategy = TruncationStrategy.HEAD,
) -> tuple[list, int]:
    """
    Truncate array to max_items using specified strategy.

    Returns:
        Tuple of (truncated array, number of items removed)
    """
    if len(arr) <= max_items:
        return arr, 0

    removed = len(arr) - max_items

    match strategy:
        case TruncationStrategy.HEAD:
            return arr[:max_items], removed
        case TruncationStrategy.TAIL:
            return arr[-max_items:], removed
        case TruncationStrategy.SAMPLE:
            return random.sample(arr, max_items), removed
        case TruncationStrategy.BALANCED:
            half = max_items // 2
            remainder = max_items % 2
            return arr[:half + remainder] + arr[-half:], removed


def truncate_string(
    value: str,
    max_length: int,
    suffix: str = "...[truncated]"
) -> tuple[str, int]:
    """
    Truncate string to max_length.

    Returns:
        Tuple of (truncated string, chars removed)
    """
    if len(value) <= max_length:
        return value, 0

    truncate_at = max_length - len(suffix)
    if truncate_at < 0:
        truncate_at = max_length
        suffix = ""

    removed = len(value) - truncate_at
    return value[:truncate_at] + suffix, removed


def truncate_data(
    data: Any,
    config: TruncationConfig,
    preserve_paths: set[str] | None = None,
    current_path: str = "$",
) -> tuple[Any, TruncationSummary]:
    """
    Recursively truncate data structure.

    Args:
        data: Input data
        config: Truncation configuration
        preserve_paths: Paths that should not be truncated
        current_path: Current JSON path (for preserve matching)

    Returns:
        Tuple of (truncated data, summary)
    """
    summary = TruncationSummary(0, 0, 0, 0)
    preserve_paths = preserve_paths or set()

    # Check if current path is preserved
    if current_path in preserve_paths:
        return data, summary

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            child_path = f"{current_path}.{key}"
            truncated_value, child_summary = truncate_data(
                value, config, preserve_paths, child_path
            )
            result[key] = truncated_value
            _merge_summary(summary, child_summary)
        return result, summary

    elif isinstance(data, list):
        # Apply max_items truncation
        if config.max_items and len(data) > config.max_items:
            data, removed = truncate_array(data, config.max_items, config.strategy)
            summary.arrays_truncated += 1
            summary.items_removed += removed

        # Recurse into remaining items
        result = []
        for i, item in enumerate(data):
            child_path = f"{current_path}[{i}]"
            truncated_item, child_summary = truncate_data(
                item, config, preserve_paths, child_path
            )
            result.append(truncated_item)
            _merge_summary(summary, child_summary)
        return result, summary

    elif isinstance(data, str):
        # Apply string truncation
        if config.max_string_length and len(data) > config.max_string_length:
            truncated, removed = truncate_string(data, config.max_string_length)
            summary.strings_truncated += 1
            summary.chars_removed += removed
            return truncated, summary
        return data, summary

    else:
        return data, summary


def _merge_summary(target: TruncationSummary, source: TruncationSummary) -> None:
    """Merge source summary into target."""
    target.arrays_truncated += source.arrays_truncated
    target.items_removed += source.items_removed
    target.strings_truncated += source.strings_truncated
    target.chars_removed += source.chars_removed


def truncate_to_token_budget(
    data: Any,
    max_tokens: int,
    encoder: str = "cl100k_base",
    format_fn: callable = None,
) -> TruncationResult:
    """
    Iteratively truncate data to fit within token budget.

    Uses binary search on max_items to find optimal truncation.
    """
    import json

    format_fn = format_fn or (lambda d: json.dumps(d, separators=(",", ":")))

    output = format_fn(data)
    original_tokens = count_tokens(output, encoder)

    if original_tokens <= max_tokens:
        return TruncationResult(
            data=data,
            original_tokens=original_tokens,
            final_tokens=original_tokens,
            truncated=False,
        )

    # Binary search for optimal max_items
    # Start by finding arrays and their sizes
    array_sizes = _find_array_sizes(data)
    if not array_sizes:
        # No arrays to truncate, try string truncation
        config = TruncationConfig(max_string_length=100)
        truncated, summary = truncate_data(data, config)
        output = format_fn(truncated)
        return TruncationResult(
            data=truncated,
            original_tokens=original_tokens,
            final_tokens=count_tokens(output, encoder),
            truncated=True,
            summary=summary,
        )

    max_size = max(array_sizes)
    low, high = 1, max_size
    best_result = data
    best_summary = None

    while low < high:
        mid = (low + high) // 2
        config = TruncationConfig(max_items=mid)
        truncated, summary = truncate_data(data, config)
        output = format_fn(truncated)
        tokens = count_tokens(output, encoder)

        if tokens <= max_tokens:
            low = mid + 1
            best_result = truncated
            best_summary = summary
        else:
            high = mid

    final_output = format_fn(best_result)
    return TruncationResult(
        data=best_result,
        original_tokens=original_tokens,
        final_tokens=count_tokens(final_output, encoder),
        truncated=True,
        summary=best_summary,
    )


def _find_array_sizes(data: Any) -> list[int]:
    """Find sizes of all arrays in data structure."""
    sizes = []

    if isinstance(data, list):
        sizes.append(len(data))
        for item in data:
            sizes.extend(_find_array_sizes(item))
    elif isinstance(data, dict):
        for value in data.values():
            sizes.extend(_find_array_sizes(value))

    return sizes
```

### CLI Integration

```python
@click.option(
    "--max-tokens",
    type=int,
    help="Maximum tokens in output (requires tiktoken).",
)
@click.option(
    "--max-items",
    type=int,
    help="Maximum items per array.",
)
@click.option(
    "--max-string-length",
    type=int,
    help="Maximum length for string values.",
)
@click.option(
    "--truncation-strategy",
    type=click.Choice(["head", "tail", "sample", "balanced"]),
    default="head",
    help="How to select items when truncating arrays.",
)
@click.option(
    "--preserve",
    multiple=True,
    help="JSON paths to preserve from truncation (e.g., '$.id,$.name').",
)
```

### Examples

**Token budget truncation:**
```bash
# Fit large API response into 2000 tokens
$ llm-fmt large-response.json --max-tokens 2000

# Output shows summary
# Truncated: 3 arrays, 450 items removed, fits in 1,987 tokens
```

**Array limiting:**
```bash
# Keep first 10 items from each array
$ llm-fmt data.json --max-items 10

# Random sample of 5 items
$ llm-fmt data.json --max-items 5 --truncation-strategy sample

# Balanced: keep items from start and end
$ llm-fmt data.json --max-items 10 --truncation-strategy balanced
```

**String truncation:**
```bash
# Truncate long descriptions
$ llm-fmt articles.json --max-string-length 200
```

**Preserve important fields:**
```bash
# Truncate arrays but keep id and error fields intact
$ llm-fmt logs.json --max-items 5 --preserve "$.id" --preserve "$.error"
```

**Combined:**
```bash
# Aggressive truncation for minimal context
$ llm-fmt huge-dataset.json \
    --max-tokens 1000 \
    --max-items 5 \
    --max-string-length 100 \
    --preserve "$.metadata.id"
```

### Smart Summaries

When `--verbose` is enabled, show what was truncated:

```
Truncation Summary:
  Arrays truncated: 3
  Items removed: 450 (from 500 total)
  Strings truncated: 12
  Characters removed: 15,230

  Token reduction: 3,247 → 1,987 (39% reduction)
```

## Acceptance Criteria

- [ ] `--max-tokens N` produces output within token budget
- [ ] `--max-items N` limits all arrays to N items
- [ ] `--max-string-length N` truncates long strings with indicator
- [ ] All four truncation strategies work correctly
- [ ] `--preserve` protects specified paths from truncation
- [ ] Summary shows what was truncated when `--verbose` used
- [ ] Works correctly with all output formats (TOON, YAML, JSON, TSV)
- [ ] Graceful fallback when tiktoken unavailable (for --max-tokens)

## Test Cases

```python
def test_truncate_array_head():
    arr = [1, 2, 3, 4, 5]
    result, removed = truncate_array(arr, 3, TruncationStrategy.HEAD)
    assert result == [1, 2, 3]
    assert removed == 2

def test_truncate_array_tail():
    arr = [1, 2, 3, 4, 5]
    result, removed = truncate_array(arr, 3, TruncationStrategy.TAIL)
    assert result == [3, 4, 5]
    assert removed == 2

def test_truncate_array_balanced():
    arr = [1, 2, 3, 4, 5, 6]
    result, removed = truncate_array(arr, 4, TruncationStrategy.BALANCED)
    assert result == [1, 2, 5, 6]
    assert removed == 2

def test_truncate_string():
    text = "This is a very long string that needs truncation"
    result, removed = truncate_string(text, 20)
    assert len(result) == 20
    assert result.endswith("...[truncated]") or len(result) <= 20

def test_max_items_nested():
    data = {
        "users": [{"id": i} for i in range(100)],
        "logs": [{"msg": f"log{i}"} for i in range(50)],
    }
    config = TruncationConfig(max_items=10)
    result, summary = truncate_data(data, config)
    assert len(result["users"]) == 10
    assert len(result["logs"]) == 10
    assert summary.arrays_truncated == 2
    assert summary.items_removed == 130

def test_preserve_paths():
    data = {
        "id": "12345",
        "items": [1, 2, 3, 4, 5],
        "metadata": {"important": "keep this"}
    }
    config = TruncationConfig(max_items=2)
    preserve = {"$.id", "$.metadata"}
    result, _ = truncate_data(data, config, preserve)
    assert result["id"] == "12345"
    assert result["metadata"] == {"important": "keep this"}
    assert len(result["items"]) == 2

def test_token_budget_truncation():
    data = [{"id": i, "name": f"Item {i}"} for i in range(1000)]
    result = truncate_to_token_budget(data, max_tokens=500)
    assert result.truncated is True
    assert result.final_tokens <= 500
    assert result.final_tokens < result.original_tokens

def test_no_truncation_needed():
    data = {"small": "data"}
    result = truncate_to_token_budget(data, max_tokens=1000)
    assert result.truncated is False
    assert result.data == data
```

## Dependencies

- `tiktoken>=0.7` (optional, for `--max-tokens`)
- Existing `llm_fmt.tokens` module
- Existing `llm_fmt.filter` module

## Notes

- Token budget truncation uses binary search for efficiency
- Consider caching token counts during iterative truncation
- `--preserve` uses JSON path syntax compatible with dpath
- Random sampling (`--truncation-strategy sample`) uses fixed seed for reproducibility in tests
- Future enhancement: priority-based truncation using field importance scores
- Future enhancement: content-aware truncation (e.g., keep unique values, deduplicate)
