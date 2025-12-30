"""Tests for TOON output encoding."""

import pytest

from llm_fmt.encoders import ToonEncoder
from llm_fmt.errors import EncodeError


class TestToonEncoderBasics:
    """Basic TOON encoding tests."""

    def test_simple_object(self) -> None:
        """Test encoding a single dict."""
        encoder = ToonEncoder()
        data = {"name": "Alice", "age": 30}
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "name|age"
        assert lines[1] == "Alice|30"

    def test_empty_object(self) -> None:
        """Test encoding empty dict."""
        encoder = ToonEncoder()
        assert encoder.encode({}) == ""

    def test_uniform_array(self) -> None:
        """Test encoding uniform array of objects."""
        encoder = ToonEncoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "id|name"
        assert lines[1] == "1|Alice"
        assert lines[2] == "2|Bob"

    def test_empty_array(self) -> None:
        """Test encoding empty array."""
        encoder = ToonEncoder()
        assert encoder.encode([]) == ""

    def test_array_empty_objects(self) -> None:
        """Test encoding array of empty dicts."""
        encoder = ToonEncoder()
        assert encoder.encode([{}, {}]) == ""


class TestToonEncoderValues:
    """Tests for TOON value encoding."""

    def test_null_value(self) -> None:
        """Test null encoding."""
        encoder = ToonEncoder()
        result = encoder.encode({"x": None})
        assert "null" in result

    def test_boolean_values(self) -> None:
        """Test boolean encoding."""
        encoder = ToonEncoder()
        data = [{"active": True}, {"active": False}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "active"
        assert lines[1] == "true"
        assert lines[2] == "false"

    def test_numeric_values(self) -> None:
        """Test numeric encoding."""
        encoder = ToonEncoder()
        data = {"int": 42, "float": 3.14, "negative": -1}
        result = encoder.encode(data)
        assert "42" in result
        assert "3.14" in result
        assert "-1" in result

    def test_primitive_value(self) -> None:
        """Test encoding a primitive (non-object, non-list)."""
        encoder = ToonEncoder()
        assert encoder.encode(42) == "42"
        assert encoder.encode("hello") == "hello"
        true_val = True
        assert encoder.encode(true_val) == "true"
        assert encoder.encode(None) == "null"


class TestToonEncoderNested:
    """Tests for nested structure encoding."""

    def test_nested_dict(self) -> None:
        """Test nested dict is JSON-encoded inline."""
        encoder = ToonEncoder()
        data = {"config": {"host": "localhost", "port": 5432}}
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "config"
        # Nested dict serialized as JSON
        assert '{"host":"localhost","port":5432}' in lines[1]

    def test_nested_array(self) -> None:
        """Test nested array is JSON-encoded inline."""
        encoder = ToonEncoder()
        data = {"tags": ["python", "json"]}
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "tags"
        assert '["python","json"]' in lines[1]

    def test_array_with_nested_values(self) -> None:
        """Test array of objects with nested values."""
        encoder = ToonEncoder()
        data = [
            {"id": 1, "meta": {"created": "2024-01-01"}},
            {"id": 2, "meta": {"created": "2024-01-02"}},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "id|meta"
        assert '{"created":"2024-01-01"}' in lines[1]
        assert '{"created":"2024-01-02"}' in lines[2]


class TestToonEncoderEscaping:
    """Tests for special character escaping."""

    def test_escape_pipe(self) -> None:
        """Test pipe character is escaped."""
        encoder = ToonEncoder()
        data = {"msg": "hello|world"}
        result = encoder.encode(data)
        assert "hello\\|world" in result

    def test_escape_newline(self) -> None:
        """Test newline is escaped."""
        encoder = ToonEncoder()
        data = {"text": "line1\nline2"}
        result = encoder.encode(data)
        assert "line1\\nline2" in result

    def test_escape_carriage_return(self) -> None:
        """Test carriage return is escaped."""
        encoder = ToonEncoder()
        data = {"text": "line1\rline2"}
        result = encoder.encode(data)
        assert "line1\\rline2" in result

    def test_escape_backslash(self) -> None:
        """Test backslash is escaped."""
        encoder = ToonEncoder()
        data = {"path": "C:\\Users"}
        result = encoder.encode(data)
        assert "C:\\\\Users" in result

    def test_escape_order(self) -> None:
        """Test backslash is escaped before other chars."""
        encoder = ToonEncoder()
        # A backslash followed by a pipe
        data = {"text": "a\\|b"}
        result = encoder.encode(data)
        # Should become a\\\\|b, then a\\\\\\|b
        assert "a\\\\\\|b" in result

    def test_no_escape_regular_string(self) -> None:
        """Test regular strings are not escaped."""
        encoder = ToonEncoder()
        data = {"name": "Alice"}
        result = encoder.encode(data)
        assert "Alice" in result
        assert "\\" not in result


class TestToonEncoderNonUniform:
    """Tests for non-uniform data handling."""

    def test_non_uniform_keys(self) -> None:
        """Test array with different keys in each object."""
        encoder = ToonEncoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "email": "bob@example.com"},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        # Header should have all unique keys
        assert lines[0] == "id|name|email"
        # Missing values should be null
        assert lines[1] == "1|Alice|null"
        assert lines[2] == "2|null|bob@example.com"

    def test_array_of_primitives(self) -> None:
        """Test array of primitives encodes one per line."""
        encoder = ToonEncoder()
        data = [1, 2, 3]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines == ["1", "2", "3"]

    def test_array_of_strings(self) -> None:
        """Test array of strings."""
        encoder = ToonEncoder()
        data = ["apple", "banana", "cherry"]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines == ["apple", "banana", "cherry"]

    def test_mixed_array_raises(self) -> None:
        """Test mixed array of objects and primitives raises."""
        encoder = ToonEncoder()
        data = [{"id": 1}, "string", 42]

        with pytest.raises(EncodeError, match="mixed arrays"):
            encoder.encode(data)
