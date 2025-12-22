# Task 012: Analysis Mode (--analyze)

**Phase**: 2 - Filtering & Analysis  
**Priority**: +150
**Storypoints**: 5  
**Status**: [ ] Not started

## Objective

Implement analysis mode that compares token counts across all output formats and recommends the optimal choice.

## Requirements

- [ ] Show token counts for each format
- [ ] Calculate percentage savings vs original JSON
- [ ] Detect data shape and explain recommendation
- [ ] Pretty terminal output with optional color
- [ ] Machine-readable output option (JSON)

## Implementation Details

```python
# src/llm_fmt/analyze.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_fmt.formats import toon, compact_json, yaml_fmt
from llm_fmt.tokens import count_tokens, is_available as tiktoken_available
from llm_fmt.detection import detect_data_shape, DataShape


@dataclass
class FormatAnalysis:
    name: str
    output: str
    tokens: int
    savings_percent: float
    recommended: bool = False


@dataclass
class AnalysisReport:
    original_tokens: int
    formats: list[FormatAnalysis]
    data_shape: DataShape
    recommendation: str
    recommendation_reason: str


def analyze(data: Any, tokenizer: str = "cl100k_base") -> AnalysisReport:
    """
    Analyze data and compare format efficiency.
    
    Returns detailed report with token counts and recommendation.
    """
    # Generate all format outputs
    outputs = {
        "JSON (pretty)": json.dumps(data, indent=2),
        "Compact JSON": compact_json.encode(data),
        "YAML": yaml_fmt.encode(data),
        "TOON": toon.encode(data),
    }
    
    # Count tokens
    if not tiktoken_available():
        raise ImportError("Install tiktoken for analysis: pip install llm-fmt[analysis]")
    
    original_tokens = count_tokens(outputs["JSON (pretty)"], tokenizer)
    
    formats = []
    for name, output in outputs.items():
        tokens = count_tokens(output, tokenizer)
        savings = ((original_tokens - tokens) / original_tokens) * 100
        formats.append(FormatAnalysis(
            name=name,
            output=output,
            tokens=tokens,
            savings_percent=savings,
        ))
    
    # Detect shape and recommend
    shape = detect_data_shape(data)
    recommendation, reason = _recommend_format(shape, formats)
    
    # Mark recommended
    for f in formats:
        f.recommended = (f.name == recommendation)
    
    return AnalysisReport(
        original_tokens=original_tokens,
        formats=sorted(formats, key=lambda f: f.tokens),
        data_shape=shape,
        recommendation=recommendation,
        recommendation_reason=reason,
    )


def _recommend_format(shape: DataShape, formats: list[FormatAnalysis]) -> tuple[str, str]:
    """Determine best format based on data shape."""
    
    if shape.is_uniform_array:
        return "TOON", f"Uniform array of {shape.array_length} objects with {shape.field_count} fields"
    
    if shape.max_depth <= 2 and shape.is_mostly_primitives:
        return "YAML", "Shallow structure with mostly primitive values"
    
    # Default: pick lowest token count that's not the original
    best = min(
        (f for f in formats if f.name != "JSON (pretty)"),
        key=lambda f: f.tokens
    )
    return best.name, f"Lowest token count ({best.tokens} tokens)"
```

### CLI Output

```
$ llm-fmt data.json --analyze

╭─────────────────────────────────────────────────────────╮
│ Token Analysis (cl100k_base tokenizer)                  │
├─────────────────────────────────────────────────────────┤
│ Format          │ Tokens  │ Savings │                   │
├─────────────────┼─────────┼─────────┼───────────────────┤
│ TOON            │   1,342 │   59%   │ ← recommended     │
│ YAML            │   2,156 │   34%   │                   │
│ Compact JSON    │   2,891 │   11%   │                   │
│ JSON (pretty)   │   3,247 │    0%   │ (baseline)        │
╰─────────────────────────────────────────────────────────╯

Data shape: Uniform array of 150 objects with 8 fields each
Recommendation: TOON saves 1,905 tokens (59%) per request

Use: llm-fmt data.json --format toon
```

### JSON Output

```bash
$ llm-fmt data.json --analyze --json

{
  "original_tokens": 3247,
  "formats": [
    {"name": "TOON", "tokens": 1342, "savings_percent": 58.7, "recommended": true},
    {"name": "YAML", "tokens": 2156, "savings_percent": 33.6, "recommended": false},
    ...
  ],
  "data_shape": {
    "type": "uniform_array",
    "length": 150,
    "fields": 8
  },
  "recommendation": "TOON",
  "recommendation_reason": "Uniform array of 150 objects with 8 fields"
}
```

## Acceptance Criteria

- [ ] `--analyze` shows comparison table
- [ ] Token counts accurate per tiktoken
- [ ] Recommendation based on data shape
- [ ] `--analyze --json` outputs machine-readable format
- [ ] Colors disabled with `--no-color`
- [ ] Helpful error if tiktoken not installed

## Test Cases

```python
def test_analyze_uniform_array():
    data = [{"id": i, "name": f"item{i}"} for i in range(10)]
    report = analyze(data)
    assert report.recommendation == "TOON"
    assert any(f.name == "TOON" and f.recommended for f in report.formats)

def test_analyze_nested_config():
    data = {"db": {"host": "localhost", "port": 5432}}
    report = analyze(data)
    # TOON less beneficial for non-arrays
    assert report.data_shape.is_uniform_array is False
```

## Dependencies

- `tiktoken>=0.7`
- `rich` (optional, for pretty tables)

## Notes

- Analysis is read-only, doesn't output converted data
- Consider caching encoder for repeated analysis
- Could add cost estimation based on model pricing
- Future: benchmark actual LLM comprehension accuracy
