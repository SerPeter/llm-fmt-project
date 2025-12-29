"""Token counting integration with tiktoken."""

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


def estimate_tokens(text: str) -> int:
    """Rough token estimate without tiktoken.

    Rule of thumb: ~4 characters per token for English text.
    Less accurate but zero dependencies.

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    return len(text) // 4
