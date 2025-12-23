"""Tests for compact JSON output encoding."""

import json

from llm_fmt.encoders import JsonEncoder


class TestJsonEncoderBasics:
    """Basic JSON encoding tests."""

    def test_simple_object(self) -> None:
        """Test encoding a simple object."""
        encoder = JsonEncoder()
        data = {"name": "Alice", "age": 30}
        result = encoder.encode(data)

        assert result == '{"name":"Alice","age":30}'

    def test_empty_object(self) -> None:
        """Test encoding empty object."""
        encoder = JsonEncoder()
        assert encoder.encode({}) == "{}"

    def test_empty_array(self) -> None:
        """Test encoding empty array."""
        encoder = JsonEncoder()
        assert encoder.encode([]) == "[]"

    def test_array_of_objects(self) -> None:
        """Test encoding array of objects."""
        encoder = JsonEncoder()
        data = [{"id": 1}, {"id": 2}]
        result = encoder.encode(data)

        assert result == '[{"id":1},{"id":2}]'


class TestJsonEncoderNoWhitespace:
    """Tests to verify no whitespace in output."""

    def test_no_spaces(self) -> None:
        """Test no spaces in output."""
        encoder = JsonEncoder()
        data = {"key": "value", "nested": {"a": 1}}
        result = encoder.encode(data)

        assert " " not in result

    def test_no_newlines(self) -> None:
        """Test no newlines in output."""
        encoder = JsonEncoder()
        data = {"key": "value", "list": [1, 2, 3]}
        result = encoder.encode(data)

        assert "\n" not in result

    def test_no_tabs(self) -> None:
        """Test no tabs in output."""
        encoder = JsonEncoder()
        data = {"a": {"b": {"c": 1}}}
        result = encoder.encode(data)

        assert "\t" not in result


class TestJsonEncoderValues:
    """Tests for JSON value encoding."""

    def test_null_value(self) -> None:
        """Test null encoding."""
        encoder = JsonEncoder()
        result = encoder.encode({"x": None})

        assert result == '{"x":null}'

    def test_boolean_values(self) -> None:
        """Test boolean encoding."""
        encoder = JsonEncoder()

        assert encoder.encode({"t": True}) == '{"t":true}'
        assert encoder.encode({"f": False}) == '{"f":false}'

    def test_integer_values(self) -> None:
        """Test integer encoding."""
        encoder = JsonEncoder()

        assert encoder.encode({"n": 42}) == '{"n":42}'
        assert encoder.encode({"n": -1}) == '{"n":-1}'
        assert encoder.encode({"n": 0}) == '{"n":0}'

    def test_float_values(self) -> None:
        """Test float encoding."""
        encoder = JsonEncoder()

        assert encoder.encode({"n": 3.14}) == '{"n":3.14}'
        assert encoder.encode({"n": -0.5}) == '{"n":-0.5}'

    def test_string_values(self) -> None:
        """Test string encoding."""
        encoder = JsonEncoder()

        assert encoder.encode({"s": "hello"}) == '{"s":"hello"}'
        assert encoder.encode({"s": ""}) == '{"s":""}'

    def test_string_escaping(self) -> None:
        """Test special characters in strings are escaped."""
        encoder = JsonEncoder()

        # Quotes
        result = encoder.encode({"s": 'say "hello"'})
        assert result == '{"s":"say \\"hello\\""}'

        # Newlines
        result = encoder.encode({"s": "line1\nline2"})
        assert result == '{"s":"line1\\nline2"}'

        # Backslashes
        result = encoder.encode({"s": "a\\b"})
        assert result == '{"s":"a\\\\b"}'

    def test_primitives(self) -> None:
        """Test encoding bare primitives."""
        encoder = JsonEncoder()

        assert encoder.encode(42) == "42"
        assert encoder.encode("hello") == '"hello"'
        true_val = True
        assert encoder.encode(true_val) == "true"
        assert encoder.encode(None) == "null"


class TestJsonEncoderNested:
    """Tests for nested structures."""

    def test_nested_object(self) -> None:
        """Test deeply nested object."""
        encoder = JsonEncoder()
        data = {"a": {"b": {"c": {"d": 1}}}}
        result = encoder.encode(data)

        assert result == '{"a":{"b":{"c":{"d":1}}}}'

    def test_nested_array(self) -> None:
        """Test nested arrays."""
        encoder = JsonEncoder()
        data = [[1, 2], [3, 4]]
        result = encoder.encode(data)

        assert result == "[[1,2],[3,4]]"

    def test_mixed_nesting(self) -> None:
        """Test mixed object and array nesting."""
        encoder = JsonEncoder()
        data = {"items": [{"id": 1}, {"id": 2}], "meta": {"count": 2}}
        result = encoder.encode(data)

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == data


class TestJsonEncoderSortKeys:
    """Tests for sorted keys option."""

    def test_sorted_keys(self) -> None:
        """Test keys are sorted alphabetically."""
        encoder = JsonEncoder(sort_keys=True)
        data = {"z": 1, "a": 2, "m": 3}
        result = encoder.encode(data)

        assert result == '{"a":2,"m":3,"z":1}'

    def test_sorted_keys_nested(self) -> None:
        """Test nested objects also have sorted keys."""
        encoder = JsonEncoder(sort_keys=True)
        data = {"z": {"c": 1, "a": 2}, "a": 0}
        result = encoder.encode(data)

        assert result == '{"a":0,"z":{"a":2,"c":1}}'

    def test_unsorted_by_default(self) -> None:
        """Test keys preserve order by default."""
        encoder = JsonEncoder()
        data = {"z": 1, "a": 2, "m": 3}
        result = encoder.encode(data)

        # Should maintain insertion order
        assert result == '{"z":1,"a":2,"m":3}'

    def test_deterministic_output(self) -> None:
        """Test sorted keys produces deterministic output."""
        encoder = JsonEncoder(sort_keys=True)
        data = {"c": 3, "a": 1, "b": 2}

        # Should always produce the same result
        results = [encoder.encode(data) for _ in range(5)]
        assert all(r == '{"a":1,"b":2,"c":3}' for r in results)


class TestJsonEncoderNonStringKeys:
    """Tests for non-string key support."""

    def test_int_keys(self) -> None:
        """Test integer keys are supported."""
        encoder = JsonEncoder()
        data = {1: "one", 2: "two"}
        result = encoder.encode(data)

        # orjson converts int keys to strings
        assert result == '{"1":"one","2":"two"}'

    def test_int_keys_sorted(self) -> None:
        """Test integer keys can be sorted."""
        encoder = JsonEncoder(sort_keys=True)
        data = {3: "three", 1: "one", 2: "two"}
        result = encoder.encode(data)

        assert result == '{"1":"one","2":"two","3":"three"}'


class TestJsonEncoderValid:
    """Tests for valid JSON output."""

    def test_output_is_parseable(self) -> None:
        """Test output can be parsed back."""
        encoder = JsonEncoder()
        data = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {"a": True, "b": None},
        }
        result = encoder.encode(data)

        parsed = json.loads(result)
        assert parsed == data

    def test_roundtrip(self) -> None:
        """Test encode-decode roundtrip."""
        encoder = JsonEncoder()
        original = [
            {"id": 1, "tags": ["a", "b"]},
            {"id": 2, "tags": ["c"]},
        ]
        encoded = encoder.encode(original)
        decoded = json.loads(encoded)

        assert decoded == original


class TestJsonEncoderStreaming:
    """Tests for streaming JSON encoding."""

    def test_stream_single_item(self) -> None:
        """Test streaming with single item."""
        encoder = JsonEncoder()
        stream = iter([{"id": 1}])
        result = "".join(encoder.encode_stream(stream))

        assert result == '[{"id":1}]'

    def test_stream_multiple_items(self) -> None:
        """Test streaming with multiple items."""
        encoder = JsonEncoder()
        stream = iter([{"id": 1}, {"id": 2}, {"id": 3}])
        result = "".join(encoder.encode_stream(stream))

        assert result == '[{"id":1},{"id":2},{"id":3}]'

    def test_stream_empty(self) -> None:
        """Test streaming with no items."""
        encoder = JsonEncoder()
        stream = iter([])
        result = "".join(encoder.encode_stream(stream))

        assert result == "[]"

    def test_stream_sorted_keys(self) -> None:
        """Test streaming with sorted keys."""
        encoder = JsonEncoder(sort_keys=True)
        stream = iter([{"z": 1, "a": 2}])
        result = "".join(encoder.encode_stream(stream))

        assert result == '[{"a":2,"z":1}]'

    def test_stream_yields_chunks(self) -> None:
        """Test streaming yields separate chunks."""
        encoder = JsonEncoder()
        stream = iter([{"id": 1}, {"id": 2}])
        chunks = list(encoder.encode_stream(stream))

        assert chunks[0] == "["
        assert chunks[1] == '{"id":1}'
        assert chunks[2] == ","
        assert chunks[3] == '{"id":2}'
        assert chunks[4] == "]"
