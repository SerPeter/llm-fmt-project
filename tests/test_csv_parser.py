"""Tests for CSV parser."""

import pytest

from llm_fmt.errors import ParseError
from llm_fmt.parsers import CsvParser


class TestCsvParserBasics:
    """Basic parsing tests."""

    def test_simple_csv(self) -> None:
        """Parse simple CSV with header."""
        parser = CsvParser()
        data = b"name,age\nAlice,30\nBob,25"
        result = parser.parse(data)
        assert result == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_csv(self) -> None:
        """Parse empty CSV returns empty list."""
        parser = CsvParser()
        data = b""
        result = parser.parse(data)
        assert result == []

    def test_header_only(self) -> None:
        """Parse CSV with only header returns empty list."""
        parser = CsvParser()
        data = b"name,age,city"
        result = parser.parse(data)
        assert result == []

    def test_single_row(self) -> None:
        """Parse CSV with single data row."""
        parser = CsvParser()
        data = b"id,value\n1,test"
        result = parser.parse(data)
        assert result == [{"id": "1", "value": "test"}]

    def test_single_column(self) -> None:
        """Parse CSV with single column."""
        parser = CsvParser()
        data = b"name\nAlice\nBob"
        result = parser.parse(data)
        assert result == [{"name": "Alice"}, {"name": "Bob"}]


class TestCsvParserQuoting:
    """Tests for quoted fields."""

    def test_quoted_fields(self) -> None:
        """Parse fields with quotes."""
        parser = CsvParser()
        data = b'name,desc\n"Alice","Hello, World"'
        result = parser.parse(data)
        assert result == [{"name": "Alice", "desc": "Hello, World"}]

    def test_quotes_with_comma(self) -> None:
        """Parse quoted field containing comma."""
        parser = CsvParser()
        data = b'text\n"one, two, three"'
        result = parser.parse(data)
        assert result == [{"text": "one, two, three"}]

    def test_escaped_quotes(self) -> None:
        """Parse escaped quotes within field."""
        parser = CsvParser()
        data = b'text\n"He said ""hello"""'
        result = parser.parse(data)
        assert result == [{"text": 'He said "hello"'}]

    def test_newline_in_quoted_field(self) -> None:
        """Parse newline within quoted field."""
        parser = CsvParser()
        data = b'text\n"line1\nline2"'
        result = parser.parse(data)
        assert result == [{"text": "line1\nline2"}]


class TestCsvParserDelimiters:
    """Tests for custom delimiters."""

    def test_tab_delimiter(self) -> None:
        """Parse TSV (tab-delimited) data."""
        parser = CsvParser(delimiter="\t")
        data = b"name\tage\nAlice\t30"
        result = parser.parse(data)
        assert result == [{"name": "Alice", "age": "30"}]

    def test_semicolon_delimiter(self) -> None:
        """Parse semicolon-delimited data."""
        parser = CsvParser(delimiter=";")
        data = b"a;b;c\n1;2;3"
        result = parser.parse(data)
        assert result == [{"a": "1", "b": "2", "c": "3"}]

    def test_pipe_delimiter(self) -> None:
        """Parse pipe-delimited data."""
        parser = CsvParser(delimiter="|")
        data = b"x|y\nfoo|bar"
        result = parser.parse(data)
        assert result == [{"x": "foo", "y": "bar"}]


class TestCsvParserNoHeader:
    """Tests for headerless mode."""

    def test_no_header_returns_lists(self) -> None:
        """Without header, returns list of lists."""
        parser = CsvParser(has_header=False)
        data = b"Alice,30\nBob,25"
        result = parser.parse(data)
        assert result == [["Alice", "30"], ["Bob", "25"]]

    def test_no_header_single_row(self) -> None:
        """Single row without header."""
        parser = CsvParser(has_header=False)
        data = b"a,b,c"
        result = parser.parse(data)
        assert result == [["a", "b", "c"]]

    def test_no_header_empty(self) -> None:
        """Empty data without header."""
        parser = CsvParser(has_header=False)
        data = b""
        result = parser.parse(data)
        assert result == []


class TestCsvParserUnicode:
    """Unicode handling tests."""

    def test_unicode_content(self) -> None:
        """Parse Unicode characters."""
        parser = CsvParser()
        data = "name,city\nアリス,東京".encode("utf-8")
        result = parser.parse(data)
        assert result == [{"name": "アリス", "city": "東京"}]

    def test_emoji_content(self) -> None:
        """Parse emoji characters."""
        parser = CsvParser()
        data = "emoji,desc\n🎉,party".encode("utf-8")
        result = parser.parse(data)
        assert result == [{"emoji": "🎉", "desc": "party"}]


class TestCsvParserErrors:
    """Error handling tests."""

    def test_invalid_encoding_raises(self) -> None:
        """Invalid encoding raises ParseError."""
        parser = CsvParser()
        # Invalid UTF-8 sequence
        with pytest.raises(ParseError, match="Invalid CSV encoding"):
            parser.parse(b"\xff\xfe invalid")


class TestCsvParserEdgeCases:
    """Edge case tests."""

    def test_empty_values(self) -> None:
        """Parse rows with empty values."""
        parser = CsvParser()
        data = b"a,b,c\n1,,3\n,2,"
        result = parser.parse(data)
        assert result == [
            {"a": "1", "b": "", "c": "3"},
            {"a": "", "b": "2", "c": ""},
        ]

    def test_trailing_comma(self) -> None:
        """Parse row with trailing comma."""
        parser = CsvParser()
        data = b"a,b\n1,2,"
        result = parser.parse(data)
        # Trailing comma creates extra empty field
        assert result == [{"a": "1", "b": "2"}]

    def test_crlf_line_endings(self) -> None:
        """Parse with Windows line endings."""
        parser = CsvParser()
        data = b"name,age\r\nAlice,30\r\nBob,25"
        result = parser.parse(data)
        assert result == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
