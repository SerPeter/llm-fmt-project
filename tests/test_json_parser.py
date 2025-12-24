"""Tests for JSON input parsing."""

import json

import pytest
from click.testing import CliRunner

from llm_fmt.cli import main
from llm_fmt.errors import ParseError
from llm_fmt.parsers import JsonParser, detect_parser


class TestJsonParser:
    """Tests for JsonParser class."""

    def test_parse_valid_object(self) -> None:
        """Test parsing valid JSON object."""
        parser = JsonParser()
        result = parser.parse(b'{"key": "value", "number": 42}')
        assert result == {"key": "value", "number": 42}

    def test_parse_valid_array(self) -> None:
        """Test parsing valid JSON array."""
        parser = JsonParser()
        result = parser.parse(b'[1, 2, 3, "four"]')
        assert result == [1, 2, 3, "four"]

    def test_parse_array_of_objects(self) -> None:
        """Test parsing array of objects."""
        parser = JsonParser()
        data = b'[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
        result = parser.parse(data)
        assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    def test_parse_nested_structure(self) -> None:
        """Test parsing deeply nested JSON."""
        parser = JsonParser()
        data = b'{"level1": {"level2": {"level3": [1, 2, 3]}}}'
        result = parser.parse(data)
        assert result == {"level1": {"level2": {"level3": [1, 2, 3]}}}

    def test_parse_primitives(self) -> None:
        """Test parsing primitive JSON values."""
        parser = JsonParser()
        assert parser.parse(b'"string"') == "string"
        assert parser.parse(b"42") == 42
        assert parser.parse(b"3.14") == 3.14
        assert parser.parse(b"true") is True
        assert parser.parse(b"false") is False
        assert parser.parse(b"null") is None

    def test_parse_unicode(self) -> None:
        """Test parsing JSON with Unicode characters."""
        parser = JsonParser()
        result = parser.parse('{"emoji": "🎉", "chinese": "中文"}'.encode())
        assert result == {"emoji": "🎉", "chinese": "中文"}

    def test_parse_invalid_json_raises_parse_error(self) -> None:
        """Test that invalid JSON raises ParseError."""
        parser = JsonParser()
        with pytest.raises(ParseError, match="Invalid JSON"):
            parser.parse(b"{invalid json}")

    def test_parse_empty_raises_error(self) -> None:
        """Test that empty input raises ParseError."""
        parser = JsonParser()
        with pytest.raises(ParseError, match="Invalid JSON"):
            parser.parse(b"")

    def test_parse_truncated_json(self) -> None:
        """Test that truncated JSON raises ParseError."""
        parser = JsonParser()
        with pytest.raises(ParseError, match="Invalid JSON"):
            parser.parse(b'{"key": ')

    def test_parse_trailing_garbage(self) -> None:
        """Test that trailing garbage raises ParseError."""
        parser = JsonParser()
        with pytest.raises(ParseError, match="Invalid JSON"):
            parser.parse(b'{"key": "value"} extra')

    def test_parse_stream(self) -> None:
        """Test streaming parse (current implementation buffers)."""
        parser = JsonParser()
        chunks = [b'{"ke', b'y": ', b'"value"}']
        results = list(parser.parse_stream(iter(chunks)))
        assert results == [{"key": "value"}]


class TestDetectParser:
    """Tests for parser auto-detection."""

    def test_detect_by_json_extension(self, tmp_path) -> None:
        """Test detection by .json extension."""
        json_file = tmp_path / "test.json"
        parser = detect_parser(filename=json_file)
        assert isinstance(parser, JsonParser)

    def test_detect_by_magic_bytes_object(self) -> None:
        """Test detection from JSON object magic bytes."""
        parser = detect_parser(data=b'{"key": "value"}')
        assert isinstance(parser, JsonParser)

    def test_detect_by_magic_bytes_array(self) -> None:
        """Test detection from JSON array magic bytes."""
        parser = detect_parser(data=b"[1, 2, 3]")
        assert isinstance(parser, JsonParser)

    def test_detect_with_whitespace(self) -> None:
        """Test detection ignores leading whitespace."""
        parser = detect_parser(data=b"   \n\t{}")
        assert isinstance(parser, JsonParser)

    def test_detect_no_input_raises(self) -> None:
        """Test that no filename or data raises ValueError."""
        with pytest.raises(ValueError, match="Cannot detect format"):
            detect_parser()


class TestCliJsonInput:
    """Tests for CLI JSON input handling."""

    def test_cli_parse_json_file(self, tmp_path) -> None:
        """Test CLI parsing JSON from file."""
        json_file = tmp_path / "test.json"
        json_file.write_text('[{"id": 1, "name": "Alice"}]')

        runner = CliRunner()
        result = runner.invoke(main, [str(json_file)])

        assert result.exit_code == 0
        assert "id|name" in result.output
        assert "1|Alice" in result.output

    def test_cli_parse_stdin(self) -> None:
        """Test CLI parsing JSON from stdin."""
        runner = CliRunner()
        result = runner.invoke(main, input='[{"id": 1, "name": "Bob"}]')

        assert result.exit_code == 0
        assert "id|name" in result.output
        assert "1|Bob" in result.output

    def test_cli_nonexistent_file(self, tmp_path) -> None:
        """Test CLI error for non-existent file."""
        runner = CliRunner()
        result = runner.invoke(main, [str(tmp_path / "nonexistent.json")])

        assert result.exit_code != 0
        assert "File not found" in result.output

    def test_cli_invalid_json_error(self, tmp_path) -> None:
        """Test CLI error message for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json}")

        runner = CliRunner()
        result = runner.invoke(main, [str(bad_file)])

        assert result.exit_code != 0
        assert "error" in result.output.lower()

    def test_cli_explicit_json_format(self, tmp_path) -> None:
        """Test CLI with explicit --input-format json."""
        json_file = tmp_path / "data.txt"  # No .json extension
        json_file.write_text('[{"x": 1}]')

        runner = CliRunner()
        result = runner.invoke(main, ["--input-format", "json", str(json_file)])

        assert result.exit_code == 0
        assert "x" in result.output

    def test_cli_large_array(self, tmp_path) -> None:
        """Test CLI handles large arrays."""
        # Create array with 1000 objects
        data = [{"id": i, "value": f"item{i}"} for i in range(1000)]
        json_file = tmp_path / "large.json"
        json_file.write_text(json.dumps(data))

        runner = CliRunner()
        result = runner.invoke(main, [str(json_file)])

        assert result.exit_code == 0
        assert "id|value" in result.output
        # Check first and last items
        assert "0|item0" in result.output
        assert "999|item999" in result.output
