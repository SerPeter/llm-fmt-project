"""Tests for token counting module."""

import pytest

from llm_fmt import tokens


class TestEstimateTokens:
    """Tests for estimate_tokens function using tokenx-style heuristics."""

    def test_estimate_short_text(self) -> None:
        """Estimate tokens for short text."""
        # "Hello, this is a test." segments: Hello(1) ,(1) this(1) is(1) a(1) test(1) .(1) = 7
        estimate = tokens.estimate_tokens("Hello, this is a test.")
        assert 5 <= estimate <= 10

    def test_estimate_empty_text(self) -> None:
        """Empty text returns 0 tokens."""
        assert tokens.estimate_tokens("") == 0

    def test_estimate_long_text(self) -> None:
        """Estimate scales with text length."""
        short_estimate = tokens.estimate_tokens("Hello")
        long_estimate = tokens.estimate_tokens("Hello " * 100)
        assert long_estimate > short_estimate

    def test_whitespace_zero_tokens(self) -> None:
        """Whitespace clusters contribute 0 tokens."""
        # Only whitespace
        assert tokens.estimate_tokens("   ") == 0
        assert tokens.estimate_tokens("\n\n\n") == 0
        assert tokens.estimate_tokens("\t  \n") == 0

    def test_numbers_one_token(self) -> None:
        """Number sequences are 1 token each."""
        assert tokens.estimate_tokens("123") == 1
        assert tokens.estimate_tokens("9999999") == 1
        # Two separate numbers
        assert tokens.estimate_tokens("123 456") == 2

    def test_short_words_one_token(self) -> None:
        """Short words (≤3 chars) are 1 token."""
        assert tokens.estimate_tokens("a") == 1
        assert tokens.estimate_tokens("the") == 1
        assert tokens.estimate_tokens("is") == 1

    def test_punctuation_estimation(self) -> None:
        """Punctuation uses ceil(len/2) rule."""
        assert tokens.estimate_tokens(",") == 1
        assert tokens.estimate_tokens("...") == 2  # ceil(3/2)
        assert tokens.estimate_tokens("!?!?") == 2  # ceil(4/2)

    def test_cjk_one_token_each(self) -> None:
        """CJK characters are 1 token each."""
        assert tokens.estimate_tokens("中") == 1
        assert tokens.estimate_tokens("中文") == 2
        assert tokens.estimate_tokens("日本語") == 3

    def test_json_structure(self) -> None:
        """JSON structure estimation."""
        json_text = '{"name":"John","age":30}'
        estimate = tokens.estimate_tokens(json_text)
        # Should be reasonable for structured data
        assert 5 <= estimate <= 15

    def test_minified_vs_pretty_json(self) -> None:
        """Minified JSON should have similar or fewer tokens than pretty."""
        minified = '{"a":1,"b":2}'
        pretty = '{\n  "a": 1,\n  "b": 2\n}'
        # Whitespace is 0 tokens, so pretty might be similar
        min_est = tokens.estimate_tokens(minified)
        pretty_est = tokens.estimate_tokens(pretty)
        # Both should be reasonable
        assert min_est > 0
        assert pretty_est >= min_est  # Pretty has same content, whitespace is 0


class TestIsAvailable:
    """Tests for is_available function."""

    def test_is_available_returns_bool(self) -> None:
        """is_available returns a boolean."""
        result = tokens.is_available()
        assert isinstance(result, bool)


class TestCountTokens:
    """Tests for count_tokens with tiktoken."""

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_count_tokens_hello_world(self) -> None:
        """Count tokens for known text."""
        # "Hello, world!" tokenizes to 4 tokens in cl100k_base
        count = tokens.count_tokens("Hello, world!")
        assert count == 4

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_count_tokens_empty(self) -> None:
        """Empty text has 0 tokens."""
        assert tokens.count_tokens("") == 0

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_count_tokens_different_tokenizers(self) -> None:
        """Different tokenizers may give different counts."""
        text = "Test text for tokenization"
        cl_count = tokens.count_tokens(text, "cl100k_base")
        o2_count = tokens.count_tokens(text, "o200k_base")
        # Both should return reasonable counts (may differ)
        assert cl_count > 0
        assert o2_count > 0

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_count_tokens_json_data(self) -> None:
        """Count tokens for JSON-like output."""
        json_text = '{"name": "John", "age": 30}'
        count = tokens.count_tokens(json_text)
        assert count > 0


class TestCountTokensSafe:
    """Tests for count_tokens_safe function."""

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_count_tokens_safe_returns_int(self) -> None:
        """count_tokens_safe returns int when available."""
        result = tokens.count_tokens_safe("Hello, world!")
        assert result == 4

    def test_count_tokens_safe_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """count_tokens_safe returns None when tiktoken unavailable."""
        # Mock count_tokens to raise ImportError
        def mock_count_tokens(text: str, tokenizer: str = "cl100k_base") -> int:
            raise ImportError("No module named 'tiktoken'")

        monkeypatch.setattr(tokens, "count_tokens", mock_count_tokens)
        result = tokens.count_tokens_safe("test")
        assert result is None


class TestGetEncoder:
    """Tests for encoder caching."""

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_get_encoder_caches(self) -> None:
        """Encoder instances are cached."""
        enc1 = tokens.get_encoder("cl100k_base")
        enc2 = tokens.get_encoder("cl100k_base")
        assert enc1 is enc2

    @pytest.mark.skipif(not tokens.is_available(), reason="tiktoken not installed")
    def test_get_encoder_different_tokenizers(self) -> None:
        """Different tokenizers return different encoders."""
        enc_cl = tokens.get_encoder("cl100k_base")
        enc_o2 = tokens.get_encoder("o200k_base")
        assert enc_cl is not enc_o2


class TestTokenizers:
    """Tests for tokenizer constants."""

    def test_tokenizers_dict_has_entries(self) -> None:
        """TOKENIZERS dict has expected entries."""
        assert "cl100k_base" in tokens.TOKENIZERS
        assert "o200k_base" in tokens.TOKENIZERS
        assert "p50k_base" in tokens.TOKENIZERS

    def test_default_tokenizer(self) -> None:
        """DEFAULT_TOKENIZER is valid."""
        assert tokens.DEFAULT_TOKENIZER in tokens.TOKENIZERS
