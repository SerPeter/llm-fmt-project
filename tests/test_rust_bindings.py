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


class TestTruncationFilter:
    """Test truncation filtering."""

    def test_max_items_head(self):
        """Test max_items with head strategy (default)."""
        data = b'[1, 2, 3, 4, 5]'
        result = convert(data, format="json", max_items=3)
        assert result == "[1,2,3]"

    def test_max_items_tail(self):
        """Test max_items with tail strategy."""
        data = b'[1, 2, 3, 4, 5]'
        result = convert(data, format="json", max_items=3, truncation_strategy="tail")
        assert result == "[3,4,5]"

    def test_max_items_balanced(self):
        """Test max_items with balanced strategy."""
        data = b'[1, 2, 3, 4, 5, 6]'
        result = convert(data, format="json", max_items=4, truncation_strategy="balanced")
        assert result == "[1,2,5,6]"

    def test_max_items_nested(self):
        """Test max_items on nested arrays."""
        data = b'{"users": [1, 2, 3, 4, 5], "logs": [6, 7, 8]}'
        result = convert(data, format="json", max_items=2)
        assert '"users":[1,2]' in result
        assert '"logs":[6,7]' in result

    def test_max_string_length(self):
        """Test max_string_length truncation."""
        data = b'{"description": "This is a very long string that should be truncated"}'
        result = convert(data, format="json", max_string_length=20)
        assert "...[truncated]" in result
        # Description should be truncated
        assert "very long string" not in result

    def test_max_string_length_short_strings_unchanged(self):
        """Test that short strings are not truncated."""
        data = b'{"name": "Alice"}'
        result = convert(data, format="json", max_string_length=100)
        assert result == '{"name":"Alice"}'

    def test_preserve_paths(self):
        """Test preserve option protects paths from truncation."""
        data = b'{"important": [1, 2, 3, 4, 5], "other": [6, 7, 8, 9, 10]}'
        result = convert(
            data,
            format="json",
            max_items=2,
            preserve=["$.important"],
        )
        # important should be preserved (all 5 items)
        assert '"important":[1,2,3,4,5]' in result
        # other should be truncated to 2 items
        assert '"other":[6,7]' in result

    def test_invalid_truncation_strategy(self):
        """Test that invalid truncation strategy raises error."""
        with pytest.raises(ValueError, match="[Uu]nknown truncation strategy"):
            convert(b"[1, 2, 3]", format="json", max_items=2, truncation_strategy="invalid")

    def test_no_truncation_when_within_limits(self):
        """Test that data within limits is unchanged."""
        data = b'[1, 2, 3]'
        result = convert(data, format="json", max_items=10)
        assert result == "[1,2,3]"


class TestAnalysis:
    """Test analysis functionality."""

    def test_analyze_uniform_array(self):
        """Test analysis of uniform array data."""
        from llm_fmt import analyze

        data = b'[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
        result = analyze(data, output_json=True)

        assert result["recommendation"] == "TOON"
        assert result["data_shape"]["is_uniform_array"] is True
        assert result["data_shape"]["array_length"] == 2
        assert len(result["formats"]) >= 4

    def test_analyze_flat_object(self):
        """Test analysis of flat object data."""
        from llm_fmt import analyze

        data = b'{"host": "localhost", "port": 5432}'
        result = analyze(data, output_json=True)

        assert result["recommendation"] == "YAML"
        assert result["data_shape"]["is_array"] is False

    def test_analyze_string_output(self):
        """Test analysis with string output format."""
        from llm_fmt import analyze

        data = b'[{"id": 1}, {"id": 2}]'
        result = analyze(data, output_json=False)

        assert isinstance(result, str)
        assert "Token Analysis" in result
        assert "TOON" in result

    def test_detect_shape(self):
        """Test data shape detection."""
        from llm_fmt import detect_shape

        data = b'[{"id": 1}, {"id": 2}]'
        shape = detect_shape(data)

        assert shape["is_array"] is True
        assert shape["is_uniform_array"] is True
        assert shape["array_length"] == 2

    def test_select_format(self):
        """Test automatic format selection."""
        from llm_fmt import select_format

        # Uniform array -> TOON
        assert select_format(b'[{"id": 1}, {"id": 2}]') == "toon"

        # Flat object -> YAML
        assert select_format(b'{"host": "localhost"}') == "yaml"


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="[Uu]nknown"):
            convert(b"{}", format="invalid_format")

    def test_invalid_input_format_raises(self):
        with pytest.raises(ValueError, match="[Uu]nsupported"):
            convert(b"{}", input_format="invalid")
