"""Tests for format conversion pipeline."""

import pytest

from llm_fmt.encoders import ToonEncoder
from llm_fmt.parsers import JsonParser
from llm_fmt.pipeline import Pipeline, PipelineBuilder


class TestPipeline:
    """Tests for the Pipeline class."""

    def test_simple_json_to_toon(self) -> None:
        """Test basic JSON to TOON conversion."""
        pipeline = Pipeline(
            parser=JsonParser(),
            encoder=ToonEncoder(),
        )
        data = b'[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
        result = pipeline.run(data)

        assert "id|name" in result
        assert "1|Alice" in result
        assert "2|Bob" in result

    def test_pipeline_builder(self) -> None:
        """Test PipelineBuilder constructs pipeline correctly."""
        pipeline = (
            PipelineBuilder()
            .with_parser(JsonParser())
            .with_format("json")
            .build()
        )

        data = b'{"key": "value"}'
        result = pipeline.run(data)
        assert result == '{"key":"value"}'

    def test_builder_requires_parser(self) -> None:
        """Test builder raises if parser not set."""
        with pytest.raises(ValueError, match="Parser not set"):
            PipelineBuilder().build()


class TestToonEncoder:
    """Tests for TOON encoding."""

    def test_uniform_array(self) -> None:
        """Test encoding uniform array of objects."""
        encoder = ToonEncoder()
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
        ]
        result = encoder.encode(data)
        lines = result.split("\n")

        assert lines[0] == "id|name|active"
        assert lines[1] == "1|Alice|true"
        assert lines[2] == "2|Bob|false"

    def test_empty_array(self) -> None:
        """Test encoding empty array."""
        encoder = ToonEncoder()
        assert encoder.encode([]) == ""

    def test_non_list_raises(self) -> None:
        """Test encoding non-list raises TypeError."""
        encoder = ToonEncoder()
        with pytest.raises(TypeError, match="requires a list"):
            encoder.encode({"key": "value"})
