"""Tests for TSV output encoding."""

import pytest

from llm_fmt.encoders import TsvEncoder
from llm_fmt.errors import EncodeError


class TestTsvEncoderBasics:
    """Basic TSV encoding tests."""

    def test_uniform_array(self) -> None:
        """Test encoding uniform array of objects."""
        encoder = TsvEncoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "id\tname"
        assert lines[1] == "1\tAlice"
        assert lines[2] == "2\tBob"

    def test_empty_array(self) -> None:
        """Test encoding empty array."""
        encoder = TsvEncoder()
        assert encoder.encode([]) == ""

    def test_single_item_array(self) -> None:
        """Test encoding array with single item."""
        encoder = TsvEncoder()
        data = [{"id": 1, "name": "Alice"}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "id\tname"
        assert lines[1] == "1\tAlice"

    def test_array_empty_objects(self) -> None:
        """Test encoding array of empty dicts."""
        encoder = TsvEncoder()
        assert encoder.encode([{}]) == ""


class TestTsvEncoderValues:
    """Tests for TSV value encoding."""

    def test_null_value(self) -> None:
        """Test null encoding as empty string."""
        encoder = TsvEncoder()
        data = [{"x": None, "y": 1}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "x\ty"
        # None becomes empty string
        assert lines[1] == "\t1"

    def test_boolean_values(self) -> None:
        """Test boolean encoding."""
        encoder = TsvEncoder()
        data = [{"active": True}, {"active": False}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "active"
        assert lines[1] == "true"
        assert lines[2] == "false"

    def test_numeric_values(self) -> None:
        """Test numeric encoding."""
        encoder = TsvEncoder()
        data = [{"int": 42, "float": 3.14, "negative": -1}]
        result = encoder.encode(data)

        assert "42" in result
        assert "3.14" in result
        assert "-1" in result

    def test_missing_values(self) -> None:
        """Test missing values become empty string."""
        encoder = TsvEncoder()
        data = [
            {"a": 1, "b": 2},
            {"a": 3},  # missing "b"
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "a\tb"
        assert lines[1] == "1\t2"
        assert lines[2] == "3\t"  # empty for missing


class TestTsvEncoderEscaping:
    """Tests for special character escaping."""

    def test_escape_tab(self) -> None:
        """Test tab character is escaped."""
        encoder = TsvEncoder()
        data = [{"msg": "hello\tworld"}]
        result = encoder.encode(data)
        assert "hello\\tworld" in result

    def test_escape_newline(self) -> None:
        """Test newline is escaped."""
        encoder = TsvEncoder()
        data = [{"text": "line1\nline2"}]
        result = encoder.encode(data)
        assert "line1\\nline2" in result

    def test_escape_carriage_return(self) -> None:
        """Test carriage return is escaped."""
        encoder = TsvEncoder()
        data = [{"text": "line1\rline2"}]
        result = encoder.encode(data)
        assert "line1\\rline2" in result

    def test_escape_backslash(self) -> None:
        """Test backslash is escaped."""
        encoder = TsvEncoder()
        data = [{"path": "C:\\Users"}]
        result = encoder.encode(data)
        assert "C:\\\\Users" in result

    def test_escape_order(self) -> None:
        """Test backslash is escaped before other chars."""
        encoder = TsvEncoder()
        # A backslash followed by a tab
        data = [{"text": "a\\\tb"}]
        result = encoder.encode(data)
        # Should become a\\\\tb (backslash escaped, then tab escaped)
        assert "a\\\\\\tb" in result

    def test_no_escape_regular_string(self) -> None:
        """Test regular strings are not escaped."""
        encoder = TsvEncoder()
        data = [{"name": "Alice"}]
        result = encoder.encode(data)
        assert "Alice" in result


class TestTsvEncoderErrors:
    """Tests for error handling."""

    def test_non_list_raises(self) -> None:
        """Test non-list input raises EncodeError."""
        encoder = TsvEncoder()

        with pytest.raises(EncodeError, match="requires a list"):
            encoder.encode({"id": 1, "name": "Alice"})

    def test_primitive_raises(self) -> None:
        """Test primitive input raises EncodeError."""
        encoder = TsvEncoder()

        with pytest.raises(EncodeError, match="requires a list"):
            encoder.encode(42)

        with pytest.raises(EncodeError, match="requires a list"):
            encoder.encode("hello")

    def test_array_of_primitives_raises(self) -> None:
        """Test array of primitives raises EncodeError."""
        encoder = TsvEncoder()

        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode([1, 2, 3])

    def test_array_of_strings_raises(self) -> None:
        """Test array of strings raises EncodeError."""
        encoder = TsvEncoder()

        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode(["apple", "banana"])

    def test_mixed_array_raises(self) -> None:
        """Test mixed array of objects and primitives raises."""
        encoder = TsvEncoder()

        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode([{"id": 1}, "string", 42])


class TestTsvEncoderNestedValues:
    """Tests for handling nested values in TSV."""

    def test_nested_dict_to_string(self) -> None:
        """Test nested dict is converted to string."""
        encoder = TsvEncoder()
        data = [{"config": {"host": "localhost", "port": 5432}}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "config"
        # Nested dict becomes string representation
        assert "host" in lines[1]
        assert "localhost" in lines[1]

    def test_nested_array_to_string(self) -> None:
        """Test nested array is converted to string."""
        encoder = TsvEncoder()
        data = [{"tags": ["python", "json"]}]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert lines[0] == "tags"
        # Nested list becomes string representation
        assert "python" in lines[1]
        assert "json" in lines[1]


class TestTsvEncoderIntegration:
    """Integration tests with realistic data."""

    def test_user_data(self) -> None:
        """Test with realistic user data."""
        encoder = TsvEncoder()
        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "active": False},
            {"id": 3, "name": "Carol", "email": "carol@example.com", "active": True},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert len(lines) == 4  # 1 header + 3 rows
        assert "id" in lines[0]
        assert "name" in lines[0]
        assert "email" in lines[0]
        assert "active" in lines[0]

    def test_large_array(self) -> None:
        """Test with large array for performance."""
        encoder = TsvEncoder()
        data = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        result = encoder.encode(data)

        lines = result.split("\n")
        assert len(lines) == 101  # 1 header + 100 rows

    def test_preserves_header_order(self) -> None:
        """Test that header order matches first item's key order."""
        encoder = TsvEncoder()
        data = [
            {"z": 1, "a": 2, "m": 3},
            {"z": 4, "a": 5, "m": 6},
        ]
        result = encoder.encode(data)

        lines = result.split("\n")
        # Order should be z, a, m (first item's order)
        assert lines[0] == "z\ta\tm"
