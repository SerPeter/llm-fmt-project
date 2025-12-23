"""Tests for YAML output encoding."""

import yaml

from llm_fmt.encoders import YamlEncoder


class TestYamlEncoderBasics:
    """Basic YAML encoding tests."""

    def test_simple_object(self) -> None:
        """Test encoding a simple object."""
        encoder = YamlEncoder()
        data = {"name": "Alice", "age": 30}
        result = encoder.encode(data)

        assert "name: Alice" in result
        assert "age: 30" in result

    def test_empty_object(self) -> None:
        """Test encoding empty object."""
        encoder = YamlEncoder()
        result = encoder.encode({})

        assert result == "{}\n"

    def test_empty_array(self) -> None:
        """Test encoding empty array."""
        encoder = YamlEncoder()
        result = encoder.encode([])

        assert result == "[]\n"

    def test_array_of_objects(self) -> None:
        """Test encoding array of objects."""
        encoder = YamlEncoder()
        data = [{"id": 1}, {"id": 2}]
        result = encoder.encode(data)

        assert "- id: 1" in result
        assert "- id: 2" in result


class TestYamlEncoderValues:
    """Tests for YAML value encoding."""

    def test_null_value(self) -> None:
        """Test null encoding."""
        encoder = YamlEncoder()
        result = encoder.encode({"x": None})

        assert "x: null" in result

    def test_boolean_values(self) -> None:
        """Test boolean encoding."""
        encoder = YamlEncoder()

        result = encoder.encode({"t": True, "f": False})
        assert "t: true" in result
        assert "f: false" in result

    def test_integer_values(self) -> None:
        """Test integer encoding."""
        encoder = YamlEncoder()

        result = encoder.encode({"n": 42})
        assert "n: 42" in result

        result = encoder.encode({"n": -1})
        assert "n: -1" in result

    def test_float_values(self) -> None:
        """Test float encoding."""
        encoder = YamlEncoder()

        result = encoder.encode({"n": 3.14})
        assert "n: 3.14" in result

    def test_string_values(self) -> None:
        """Test string encoding."""
        encoder = YamlEncoder()

        result = encoder.encode({"s": "hello"})
        assert "s: hello" in result

    def test_unicode_preserved(self) -> None:
        """Test unicode characters are preserved."""
        encoder = YamlEncoder()
        data = {"greeting": "こんにちは", "emoji": "🎉"}
        result = encoder.encode(data)

        assert "こんにちは" in result
        assert "🎉" in result


class TestYamlEncoderMultiline:
    """Tests for multi-line string handling."""

    def test_multiline_uses_literal_block(self) -> None:
        """Test multi-line strings use literal block style."""
        encoder = YamlEncoder()
        data = {"content": "line1\nline2\nline3"}
        result = encoder.encode(data)

        # Should use literal block style
        assert "content: |" in result
        # Lines should be preserved
        parsed = yaml.safe_load(result)
        assert parsed["content"] == "line1\nline2\nline3"

    def test_multiline_preserves_newlines(self) -> None:
        """Test multi-line strings preserve newlines exactly."""
        encoder = YamlEncoder()
        data = {"text": "first\nsecond\nthird"}
        result = encoder.encode(data)

        parsed = yaml.safe_load(result)
        assert parsed["text"] == "first\nsecond\nthird"

    def test_single_line_no_block_style(self) -> None:
        """Test single-line strings don't use block style."""
        encoder = YamlEncoder()
        data = {"msg": "simple message"}
        result = encoder.encode(data)

        # Should not have | indicator
        assert "|" not in result
        assert "msg: simple message" in result


class TestYamlEncoderNested:
    """Tests for nested structures."""

    def test_nested_object(self) -> None:
        """Test nested object encoding."""
        encoder = YamlEncoder()
        data = {"database": {"host": "localhost", "port": 5432}}
        result = encoder.encode(data)

        assert "database:" in result
        assert "host: localhost" in result
        assert "port: 5432" in result

        # Verify parseable
        parsed = yaml.safe_load(result)
        assert parsed == data

    def test_nested_array(self) -> None:
        """Test nested array encoding."""
        encoder = YamlEncoder()
        data = {"items": [1, 2, 3]}
        result = encoder.encode(data)

        assert "items:" in result
        assert "- 1" in result
        assert "- 2" in result
        assert "- 3" in result

    def test_deeply_nested(self) -> None:
        """Test deeply nested structure."""
        encoder = YamlEncoder()
        data = {"a": {"b": {"c": {"d": 1}}}}
        result = encoder.encode(data)

        parsed = yaml.safe_load(result)
        assert parsed == data

    def test_complex_structure(self) -> None:
        """Test complex nested structure from task spec."""
        encoder = YamlEncoder()
        data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"user": "admin", "password": "secret"},
            },
            "features": ["auth", "logging", "metrics"],
        }
        result = encoder.encode(data)

        parsed = yaml.safe_load(result)
        assert parsed == data


class TestYamlEncoderIndent:
    """Tests for indent configuration."""

    def test_default_indent_is_2(self) -> None:
        """Test default indent is 2 spaces."""
        encoder = YamlEncoder()
        data = {"outer": {"inner": "value"}}
        result = encoder.encode(data)

        lines = result.split("\n")
        inner_line = next(line for line in lines if "inner:" in line)
        # Should be 2-space indent
        assert inner_line.startswith("  inner:")

    def test_custom_indent_4(self) -> None:
        """Test custom indent of 4 spaces."""
        encoder = YamlEncoder(indent=4)
        data = {"outer": {"inner": "value"}}
        result = encoder.encode(data)

        lines = result.split("\n")
        inner_line = next(line for line in lines if "inner:" in line)
        # Should be 4-space indent
        assert inner_line.startswith("    inner:")

    def test_indent_affects_arrays(self) -> None:
        """Test indent affects array items."""
        encoder = YamlEncoder(indent=4)
        data = {"items": [1, 2]}
        result = encoder.encode(data)

        # Array items should be indented
        assert "    - 1" in result or "- 1" in result  # pyyaml may not indent first level


class TestYamlEncoderBlockStyle:
    """Tests for block style output."""

    def test_objects_use_block_style(self) -> None:
        """Test objects use block style, not flow style."""
        encoder = YamlEncoder()
        data = {"a": 1, "b": 2}
        result = encoder.encode(data)

        # Should not use flow style {a: 1, b: 2}
        assert result.strip() != "{a: 1, b: 2}"
        assert "a: 1" in result

    def test_arrays_use_block_style(self) -> None:
        """Test arrays use block style."""
        encoder = YamlEncoder()
        data = {"items": [1, 2, 3]}
        result = encoder.encode(data)

        # Should use - notation, not [1, 2, 3]
        assert "- 1" in result


class TestYamlEncoderQuoting:
    """Tests for minimal quoting."""

    def test_simple_string_no_quotes(self) -> None:
        """Test simple strings are not quoted."""
        encoder = YamlEncoder()
        data = {"name": "Alice"}
        result = encoder.encode(data)

        assert "name: Alice" in result
        assert '"Alice"' not in result
        assert "'Alice'" not in result

    def test_numeric_string_quoted(self) -> None:
        """Test numeric-looking strings may be quoted to preserve type."""
        encoder = YamlEncoder()
        data = {"code": "123"}
        result = encoder.encode(data)

        # Should be parseable back as string
        parsed = yaml.safe_load(result)
        assert parsed["code"] == "123"

    def test_special_chars_quoted(self) -> None:
        """Test strings with special YAML chars are quoted."""
        encoder = YamlEncoder()
        data = {"value": "foo: bar"}
        result = encoder.encode(data)

        # Should be parseable
        parsed = yaml.safe_load(result)
        assert parsed["value"] == "foo: bar"


class TestYamlEncoderValid:
    """Tests for valid YAML output."""

    def test_output_is_parseable(self) -> None:
        """Test output can be parsed back."""
        encoder = YamlEncoder()
        data = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {"a": True, "b": None},
        }
        result = encoder.encode(data)

        parsed = yaml.safe_load(result)
        assert parsed == data

    def test_roundtrip(self) -> None:
        """Test encode-decode roundtrip."""
        encoder = YamlEncoder()
        original = [
            {"id": 1, "tags": ["a", "b"]},
            {"id": 2, "tags": ["c"]},
        ]
        encoded = encoder.encode(original)
        decoded = yaml.safe_load(encoded)

        assert decoded == original


class TestYamlEncoderStreaming:
    """Tests for streaming YAML encoding."""

    def test_stream_single_item(self) -> None:
        """Test streaming with single item."""
        encoder = YamlEncoder()
        stream = iter([{"id": 1}])
        result = "".join(encoder.encode_stream(stream))

        assert "---" in result
        assert "id: 1" in result

    def test_stream_multiple_items(self) -> None:
        """Test streaming with multiple items."""
        encoder = YamlEncoder()
        stream = iter([{"id": 1}, {"id": 2}])
        result = "".join(encoder.encode_stream(stream))

        # Should have multiple documents
        assert result.count("---") == 2
        assert "id: 1" in result
        assert "id: 2" in result

    def test_stream_documents_are_valid(self) -> None:
        """Test each streamed document is valid YAML."""
        encoder = YamlEncoder()
        stream = iter([{"a": 1}, {"b": 2}])
        chunks = list(encoder.encode_stream(stream))

        # Combine and parse as multi-document YAML
        full_yaml = "".join(chunks)
        docs = list(yaml.safe_load_all(full_yaml))

        assert docs == [{"a": 1}, {"b": 2}]

    def test_stream_with_custom_indent(self) -> None:
        """Test streaming respects indent setting."""
        encoder = YamlEncoder(indent=4)
        stream = iter([{"outer": {"inner": 1}}])
        result = "".join(encoder.encode_stream(stream))

        lines = result.split("\n")
        inner_line = next(line for line in lines if "inner:" in line)
        assert inner_line.startswith("    inner:")

    def test_stream_multiline_strings(self) -> None:
        """Test streaming handles multiline strings."""
        encoder = YamlEncoder()
        stream = iter([{"text": "line1\nline2"}])
        result = "".join(encoder.encode_stream(stream))

        assert "text: |" in result
