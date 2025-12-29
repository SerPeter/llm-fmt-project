"""Token counting integration with tiktoken."""

from __future__ import annotations

import re
from functools import lru_cache
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tiktoken


# Regex patterns for tokenx-style estimation
_SEGMENT_PATTERN = re.compile(r"(\s+|[^\s\w]+|\w+)")  # Keep consecutive punctuation together
_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
_NUMBER_PATTERN = re.compile(r"^\d+$")
_PUNCTUATION_PATTERN = re.compile(r"^[^\w\s]+$")

# Common JSON/structured data token patterns (typically 1 token each)
_JSON_COMMON_TOKENS = frozenset({
    # 2-char patterns
    '{"', '"}', '":', ',"', '",', ":[", "],", ":{", "},", "}]", "[{",
    "{{", "}}", "[[", "]]", "::", ",,", '["', '"]', "..", "--", "==",
    # 3-char patterns
    '":"', '"},', '":[', '"]}', '"],', '"}]', "}}}", "{{{", "]}}", '":{',
    "...", "---", "===", ">>>", "<<<",
    # 4-char patterns
    '":{"', '"},"', '"],[', '":["', '"]:"',
})

TOKENIZERS = {
    "cl100k_base": "GPT-4, GPT-3.5-turbo, text-embedding-ada-002",
    "o200k_base": "GPT-4o, GPT-4o-mini",
    "p50k_base": "Codex, text-davinci-002/003",
}

DEFAULT_TOKENIZER = "cl100k_base"


def is_available() -> bool:
    """Check if tiktoken is installed."""
    try:
        import tiktoken  # noqa: F401, PLC0415

        return True  # noqa: TRY300
    except ImportError:
        return False


@lru_cache(maxsize=4)
def get_encoder(name: str = DEFAULT_TOKENIZER) -> tiktoken.Encoding:
    """Get a cached tokenizer encoder.

    Args:
        name: Tokenizer name.

    Returns:
        Tiktoken encoding instance.

    Raises:
        ImportError: If tiktoken is not installed.
        ValueError: If tokenizer name is invalid.
    """
    import tiktoken  # noqa: PLC0415

    return tiktoken.get_encoding(name)


def count_tokens(text: str, tokenizer: str = DEFAULT_TOKENIZER) -> int:
    """Count tokens in text.

    Args:
        text: Input text.
        tokenizer: Tokenizer name (cl100k_base, o200k_base, etc.).

    Returns:
        Token count.

    Raises:
        ImportError: If tiktoken not installed.
    """
    encoder = get_encoder(tokenizer)
    return len(encoder.encode(text))


def count_tokens_safe(text: str, tokenizer: str = DEFAULT_TOKENIZER) -> int | None:
    """Count tokens, returning None if tiktoken unavailable.

    Args:
        text: Input text.
        tokenizer: Tokenizer name.

    Returns:
        Token count or None if tiktoken is not available.
    """
    try:
        return count_tokens(text, tokenizer)
    except ImportError:
        return None


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Estimate token count using tokenx-style heuristics.

    Uses segment-based analysis for ~94% accuracy compared to full tokenizers.
    Based on https://github.com/johannschopplich/tokenx algorithm.

    Segment rules:
    - Whitespace clusters: 0 tokens
    - CJK characters: 1 token each
    - Number sequences: 1 token
    - Short segments (≤3 chars): 1 token
    - Punctuation: ceil(len / 2) tokens
    - Alphanumeric: ceil(len / chars_per_token) tokens

    Args:
        text: Input text.
        chars_per_token: Average characters per token for alphanumeric text.

    Returns:
        Estimated token count.
    """
    if not text:
        return 0

    tokens = 0
    for segment in _SEGMENT_PATTERN.findall(text):
        tokens += _estimate_segment_tokens(segment, chars_per_token)

    return tokens


def _estimate_segment_tokens(segment: str, chars_per_token: float) -> int:
    """Estimate tokens for a single segment.

    Args:
        segment: Text segment to estimate.
        chars_per_token: Average characters per token.

    Returns:
        Estimated token count for segment.
    """
    # Whitespace: 0 tokens
    if segment.isspace():
        return 0

    # CJK characters: 1 token each
    cjk_count = len(_CJK_PATTERN.findall(segment))
    if cjk_count > 0:
        non_cjk = len(segment) - cjk_count
        return cjk_count + (ceil(non_cjk / chars_per_token) if non_cjk > 0 else 0)

    # Numbers: 1 token per sequence
    if _NUMBER_PATTERN.match(segment):
        return 1

    # Punctuation: check for common JSON patterns first
    if _PUNCTUATION_PATTERN.match(segment):
        return _estimate_punctuation_tokens(segment)

    # Short alphanumeric segments: 1 token (common words up to ~6 chars)
    if len(segment) <= 6:  # noqa: PLR2004
        return 1

    # Long alphanumeric: ceil(len / chars_per_token)
    return ceil(len(segment) / chars_per_token)


def _estimate_punctuation_tokens(segment: str) -> int:
    """Estimate tokens for punctuation, accounting for common JSON patterns.

    Args:
        segment: Punctuation-only segment.

    Returns:
        Estimated token count.
    """
    if not segment:
        return 0

    # Check for exact common token matches
    if segment in _JSON_COMMON_TOKENS:
        return 1

    # Try to greedily match common patterns
    tokens = 0
    i = 0
    while i < len(segment):
        matched = False
        # Try longer patterns first (4, 3, then 2 chars)
        for length in (4, 3, 2):
            if i + length <= len(segment):
                substr = segment[i : i + length]
                if substr in _JSON_COMMON_TOKENS:
                    tokens += 1
                    i += length
                    matched = True
                    break
        if not matched:
            # Single punctuation char = 1 token
            tokens += 1
            i += 1

    return tokens
