"""Regression tests for Rust bindings via Python interface."""

import pytest

# Skip all tests if Rust module not available
pytest.importorskip("llm_fmt._native")

from llm_fmt import convert, RUST_AVAILABLE, native_version


class TestModuleAvailability:
    """Test that the Rust module is properly loaded."""

    def test_rust_available(self):
        assert RUST_AVAILABLE is True

    def test_native_version(self):
        version = native_version()
        assert version == "0.1.0"


class TestJsonParsing:
    """Test JSON input parsing."""

    def test_parse_simple_object(self):
        result = convert(b'{"name": "Alice", "age": 30}', format="json")
        assert '"name":"Alice"' in result
        assert '"age":30' in result

    def test_parse_array(self):
        result = convert(b"[1, 2, 3]", format="json")
        assert result == "[1,2,3]"

    def test_parse_nested(self):
        result = convert(b'{"user": {"id": 1}}', format="json")
        assert '"user":{' in result
        assert '"id":1' in result

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="parse"):
            convert(b"not valid json", input_format="json")


class TestYamlParsing:
    """Test YAML input parsing."""

    def test_parse_simple_yaml(self):
        result = convert(b"name: Alice\nage: 30", input_format="yaml", format="json")
        assert '"name":"Alice"' in result
        assert '"age":30' in result

    def test_parse_yaml_array(self):
        result = convert(b"- 1\n- 2\n- 3", input_format="yaml", format="json")
        assert result == "[1,2,3]"


class TestXmlParsing:
    """Test XML input parsing."""

    def test_parse_simple_xml(self):
        result = convert(
            b"<root><name>Alice</name><age>30</age></root>",
            input_format="xml",
            format="json",
        )
        assert "Alice" in result
        assert "30" in result

    def test_parse_nested_xml(self):
        result = convert(
            b"<root><user><id>1</id></user></root>",
            input_format="xml",
            format="json",
        )
        assert "user" in result
        assert "1" in result


class TestCsvParsing:
    """Test CSV input parsing."""

    def test_parse_csv_with_headers(self):
        result = convert(
            b"name,age\nAlice,30\nBob,25",
            input_format="csv",
            format="json",
        )
        assert "Alice" in result
        assert "Bob" in result
        assert "30" in result

    def test_parse_tsv(self):
        result = convert(
            b"name\tage\nAlice\t30",
            input_format="tsv",
            format="json",
        )
        assert "Alice" in result
        assert "30" in result


class TestToonEncoding:
    """Test TOON output format."""

    def test_tabular_data(self):
        input_data = b'[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
        result = convert(input_data, format="toon")
        assert "@header:" in result
        assert "name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_non_tabular_compact(self):
        result = convert(b'{"key": "value"}', format="toon")
        assert "{" in result
        assert "key" in result


class TestJsonEncoding:
    """Test JSON output format."""

    def test_compact_json(self):
        result = convert(b'{"a": 1, "b": 2}', format="json")
        # Should be minified (no spaces after colons/commas in output)
        assert result == '{"a":1,"b":2}'

    def test_sort_keys(self):
        result = convert(b'{"z": 1, "a": 2}', format="json", sort_keys=True)
        # 'a' should come before 'z'
        assert result.index('"a"') < result.index('"z"')


class TestYamlEncoding:
    """Test YAML output format."""

    def test_yaml_output(self):
        result = convert(b'{"name": "Alice", "age": 30}', format="yaml")
        assert "name:" in result
        assert "Alice" in result
        assert "age:" in result

    def test_yaml_array(self):
        result = convert(b"[1, 2, 3]", format="yaml")
        assert "- 1" in result
        assert "- 2" in result


class TestTsvEncoding:
    """Test TSV output format."""

    def test_tsv_output(self):
        input_data = b'[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
        result = convert(input_data, format="tsv")
        assert "name\tage" in result or "age\tname" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_tsv_non_array_raises(self):
        with pytest.raises(ValueError, match="list"):
            convert(b'{"not": "array"}', format="tsv")


class TestCsvEncoding:
    """Test CSV output format."""

    def test_csv_output(self):
        input_data = b'[{"name": "Alice", "age": 30}]'
        result = convert(input_data, format="csv")
        assert "name" in result
        assert "Alice" in result

    def test_csv_quotes_special_chars(self):
        input_data = b'[{"text": "has, comma"}]'
        result = convert(input_data, format="csv")
        assert '"has, comma"' in result


class TestMaxDepthFilter:
    """Test max_depth filtering."""

    def test_depth_limit(self):
        deep_data = b'{"a": {"b": {"c": {"d": 1}}}}'
        result = convert(deep_data, format="json", max_depth=2)
        # At depth 2, the inner structure should be truncated
        assert "..." in result

    def test_no_depth_limit(self):
        deep_data = b'{"a": {"b": {"c": 1}}}'
        result = convert(deep_data, format="json")
        assert '"c":1' in result


class TestIncludeFilter:
    """Test include path filtering."""

    def test_simple_key_extraction(self):
        result = convert(
            b'{"users": [1, 2], "count": 2}',
            format="json",
            include="count",
        )
        assert result == "2"

    def test_nested_path(self):
        result = convert(
            b'{"data": {"value": 42}}',
            format="json",
            include="data.value",
        )
        assert result == "42"

    def test_array_index(self):
        result = convert(
            b'{"items": ["a", "b", "c"]}',
            format="json",
            include="items[1]",
        )
        assert result == '"b"'

    def test_wildcard(self):
        result = convert(
            b'{"users": [{"name": "Alice"}, {"name": "Bob"}]}',
            format="json",
            include="users[*].name",
        )
        assert "Alice" in result
        assert "Bob" in result


class TestAutoDetection:
    """Test auto-detection of input format."""

    def test_auto_detect_json(self):
        result = convert(b'{"key": "value"}', input_format="auto", format="json")
        assert '"key":"value"' in result

    def test_auto_detect_xml(self):
        result = convert(b"<root><key>value</key></root>", input_format="auto", format="json")
        assert "key" in result
        assert "value" in result


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="[Uu]nknown"):
            convert(b"{}", format="invalid_format")

    def test_invalid_input_format_raises(self):
        with pytest.raises(ValueError, match="[Uu]nsupported"):
            convert(b"{}", input_format="invalid")
