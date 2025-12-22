# Task 011: Token Counting Integration

**Phase**: 2 - Filtering & Analysis  
**Priority**: +150
**Storypoints**: 3  
**Status**: [ ] Not started

## Objective

Integrate tiktoken for accurate token counting across different LLM tokenizers.

## Requirements

- [ ] Count tokens using tiktoken library
- [ ] Support multiple tokenizers (cl100k_base, o200k_base)
- [ ] Graceful fallback if tiktoken not installed
- [ ] Fast counting for large outputs
- [ ] Expose in both CLI and Python API

## Implementation Details

```python
# src/llm_fmt/tokens.py
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tiktoken


TOKENIZERS = {
    "cl100k_base": "GPT-4, GPT-3.5-turbo, text-embedding-ada-002",
    "o200k_base": "GPT-4o, GPT-4o-mini",
    "p50k_base": "Codex, text-davinci-002/003",
}

DEFAULT_TOKENIZER = "cl100k_base"


def is_available() -> bool:
    """Check if tiktoken is installed."""
    try:
        import tiktoken
        return True
    except ImportError:
        return False


@lru_cache(maxsize=4)
def get_encoder(name: str = DEFAULT_TOKENIZER) -> "tiktoken.Encoding":
    """Get a cached tokenizer encoder."""
    import tiktoken
    return tiktoken.get_encoding(name)


def count_tokens(text: str, tokenizer: str = DEFAULT_TOKENIZER) -> int:
    """
    Count tokens in text.
    
    Args:
        text: Input text
        tokenizer: Tokenizer name (cl100k_base, o200k_base, etc.)
        
    Returns:
        Token count
        
    Raises:
        ImportError: If tiktoken not installed
    """
    encoder = get_encoder(tokenizer)
    return len(encoder.encode(text))


def count_tokens_safe(text: str, tokenizer: str = DEFAULT_TOKENIZER) -> int | None:
    """
    Count tokens, returning None if tiktoken unavailable.
    """
    try:
        return count_tokens(text, tokenizer)
    except ImportError:
        return None


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate without tiktoken.
    
    Rule of thumb: ~4 characters per token for English text.
    Less accurate but zero dependencies.
    """
    return len(text) // 4
```

### Tokenizer Selection

```python
# CLI option
@click.option(
    "--tokenizer",
    type=click.Choice(list(TOKENIZERS.keys())),
    default=DEFAULT_TOKENIZER,
    help=f"Tokenizer for counting (default: {DEFAULT_TOKENIZER})"
)

# Auto-detect based on model hint
def suggest_tokenizer(model: str | None) -> str:
    if model and "gpt-4o" in model.lower():
        return "o200k_base"
    return "cl100k_base"
```

### Performance Notes

tiktoken is implemented in Rust, so it's fast:
- ~1M tokens/second on typical hardware
- Memory efficient (streaming)
- Thread-safe with proper caching

```python
# Benchmark
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")

# Fast: encode returns list of ints
tokens = enc.encode(large_text)
count = len(tokens)

# Don't do this for just counting:
# decoded = enc.decode(tokens)  # Unnecessary work
```

## Acceptance Criteria

- [ ] `count_tokens("hello world")` returns accurate count
- [ ] Works with cl100k_base and o200k_base
- [ ] `--tokenizer` CLI option switches tokenizers
- [ ] Graceful error if tiktoken not installed
- [ ] `estimate_tokens()` works without dependencies

## Test Cases

```python
def test_count_tokens():
    # Known token counts
    assert count_tokens("Hello, world!") == 4

def test_different_tokenizers():
    text = "Test text"
    cl_count = count_tokens(text, "cl100k_base")
    o2_count = count_tokens(text, "o200k_base")
    # Counts may differ between tokenizers

def test_fallback_estimation():
    estimate = estimate_tokens("Hello, this is a test.")
    assert 4 <= estimate <= 10  # Rough range

def test_missing_tiktoken(monkeypatch):
    monkeypatch.setattr("llm_fmt.tokens.is_available", lambda: False)
    result = count_tokens_safe("test")
    assert result is None
```

## Dependencies

- `tiktoken>=0.7` (optional, in `[analysis]` extra)

## Installation

```bash
# Without token counting
pip install llm-fmt

# With token counting
pip install llm-fmt[analysis]

# Or
uv add llm-fmt --extra analysis
```

## Notes

- tiktoken requires Rust toolchain to build from source
- Pre-built wheels available for most platforms
- Cache encoder instances - creation is expensive
- Consider adding Anthropic/Claude tokenizer when available
