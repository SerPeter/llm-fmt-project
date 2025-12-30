"""Tests for CSV encoder."""

import pytest

from llm_fmt.encoders import CsvEncoder
from llm_fmt.errors import EncodeError


class TestCsvEncoderBasics:
    """Basic encoding tests."""

    def test_simple_array(self) -> None:
        """Encode simple array of objects."""
        encoder = CsvEncoder()
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = encoder.encode(data)
        assert result == "name,age\nAlice,30\nBob,25\n"

    def test_empty_array(self) -> None:
        """Encode empty array returns empty string."""
        encoder = CsvEncoder()
        result = encoder.encode([])
        assert result == ""

    def test_single_item_array(self) -> None:
        """Encode single-item array."""
        encoder = CsvEncoder()
        data = [{"id": 1, "value": "test"}]
        result = encoder.encode(data)
        assert result == "id,value\n1,test\n"

    def test_array_empty_objects(self) -> None:
        """Encode array of empty objects returns empty string."""
        encoder = CsvEncoder()
        result = encoder.encode([{}])
        assert result == ""


class TestCsvEncoderValues:
    """Value type handling tests."""

    def test_null_value(self) -> None:
        """Encode None as empty string."""
        encoder = CsvEncoder()
        data = [{"a": None}]
        result = encoder.encode(data)
        # CSV module quotes empty strings
        assert result == 'a\n""\n'

    def test_boolean_values(self) -> None:
        """Encode booleans as lowercase."""
        encoder = CsvEncoder()
        data = [{"a": True, "b": False}]
        result = encoder.encode(data)
        assert result == "a,b\ntrue,false\n"

    def test_numeric_values(self) -> None:
        """Encode numeric values."""
        encoder = CsvEncoder()
        data = [{"int": 42, "float": 3.14}]
        result = encoder.encode(data)
        assert result == "int,float\n42,3.14\n"

    def test_missing_values(self) -> None:
        """Handle missing keys."""
        encoder = CsvEncoder()
        data = [{"a": 1, "b": 2}, {"a": 3}]
        result = encoder.encode(data)
        lines = result.strip().split("\n")
        assert lines[0] == "a,b"
        assert lines[2] == "3,"


class TestCsvEncoderQuoting:
    """CSV quoting behavior tests."""

    def test_quote_comma_in_value(self) -> None:
        """Quote values containing commas."""
        encoder = CsvEncoder()
        data = [{"text": "one, two, three"}]
        result = encoder.encode(data)
        assert result == 'text\n"one, two, three"\n'

    def test_quote_newline_in_value(self) -> None:
        """Quote values containing newlines."""
        encoder = CsvEncoder()
        data = [{"text": "line1\nline2"}]
        result = encoder.encode(data)
        assert result == 'text\n"line1\nline2"\n'

    def test_quote_double_quote_in_value(self) -> None:
        """Escape and quote values containing quotes."""
        encoder = CsvEncoder()
        data = [{"text": 'He said "hello"'}]
        result = encoder.encode(data)
        assert result == 'text\n"He said ""hello"""\n'

    def test_no_quote_simple_string(self) -> None:
        """Don't quote simple strings."""
        encoder = CsvEncoder()
        data = [{"text": "hello world"}]
        result = encoder.encode(data)
        assert result == "text\nhello world\n"


class TestCsvEncoderErrors:
    """Error handling tests."""

    def test_non_list_raises(self) -> None:
        """Non-list data raises EncodeError."""
        encoder = CsvEncoder()
        with pytest.raises(EncodeError, match="list of objects"):
            encoder.encode({"key": "value"})

    def test_primitive_raises(self) -> None:
        """Primitive data raises EncodeError."""
        encoder = CsvEncoder()
        with pytest.raises(EncodeError, match="list of objects"):
            encoder.encode("just a string")

    def test_array_of_primitives_raises(self) -> None:
        """Array of primitives raises EncodeError."""
        encoder = CsvEncoder()
        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode([1, 2, 3])

    def test_array_of_strings_raises(self) -> None:
        """Array of strings raises EncodeError."""
        encoder = CsvEncoder()
        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode(["a", "b", "c"])

    def test_mixed_array_raises(self) -> None:
        """Mixed array raises EncodeError."""
        encoder = CsvEncoder()
        with pytest.raises(EncodeError, match="all items to be objects"):
            encoder.encode([{"a": 1}, "not a dict"])


class TestCsvEncoderNestedValues:
    """Nested value handling tests."""

    def test_nested_dict_to_string(self) -> None:
        """Nested dict converts to string representation."""
        encoder = CsvEncoder()
        data = [{"a": {"nested": "value"}}]
        result = encoder.encode(data)
        assert "nested" in result
        assert "value" in result

    def test_nested_array_to_string(self) -> None:
        """Nested array converts to string representation."""
        encoder = CsvEncoder()
        data = [{"items": [1, 2, 3]}]
        result = encoder.encode(data)
        assert "[1, 2, 3]" in result or "[1,2,3]" in result.replace(" ", "")


class TestCsvEncoderUnicode:
    """Unicode handling tests."""

    def test_unicode_content(self) -> None:
        """Preserve Unicode characters."""
        encoder = CsvEncoder()
        data = [{"name": "日本語", "emoji": "🎉"}]
        result = encoder.encode(data)
        assert "日本語" in result
        assert "🎉" in result


class TestCsvEncoderIntegration:
    """Integration tests."""

    def test_user_data(self) -> None:
        """Encode typical user data."""
        encoder = CsvEncoder()
        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "active": False},
        ]
        result = encoder.encode(data)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "id" in lines[0]
        assert "alice@example.com" in result

    def test_preserves_header_order(self) -> None:
        """Header order matches first object key order."""
        encoder = CsvEncoder()
        data = [{"z": 1, "a": 2, "m": 3}]
        result = encoder.encode(data)
        header = result.split("\n")[0]
        assert header == "z,a,m"
