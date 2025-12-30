"""Tests for pipeline module."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from llm_fmt.encoders import JsonEncoder, ToonEncoder
from llm_fmt.errors import EncodeError, ParseError
from llm_fmt.parsers import JsonParser
from llm_fmt.pipeline import Pipeline, PipelineBuilder


class TestPipeline:
    """Tests for Pipeline class."""

    def test_run_basic(self) -> None:
        """Basic pipeline run parses, filters, and encodes."""
        pipeline = (
            PipelineBuilder().with_parser(JsonParser()).with_format("json").build()
        )

        result = pipeline.run(b'{"key": "value"}')
        assert result == '{"key":"value"}'

    def test_run_parse_error_passthrough(self) -> None:
        """ParseError from parser is re-raised as-is."""
        pipeline = (
            PipelineBuilder().with_parser(JsonParser()).with_format("json").build()
        )

        with pytest.raises(ParseError):
            pipeline.run(b"invalid json")

    def test_run_generic_parse_exception_wrapped(self) -> None:
        """Generic exception during parsing is wrapped in ParseError."""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = RuntimeError("Unexpected error")

        pipeline = Pipeline(
            parser=mock_parser,
            encoder=JsonEncoder(),
        )

        with pytest.raises(ParseError, match="Unexpected error"):
            pipeline.run(b"data")

    def test_run_encode_exception_wrapped(self) -> None:
        """Exception during encoding is wrapped in EncodeError."""
        mock_encoder = MagicMock()
        mock_encoder.encode.side_effect = RuntimeError("Encoding failed")

        pipeline = Pipeline(
            parser=JsonParser(),
            encoder=mock_encoder,
        )

        with pytest.raises(EncodeError, match="Encoding failed"):
            pipeline.run(b'{"key": "value"}')


class TestPipelineBuilder:
    """Tests for PipelineBuilder class."""

    def test_build_without_parser_raises(self) -> None:
        """Building without parser raises ValueError."""
        builder = PipelineBuilder()
        builder.with_format("json")

        with pytest.raises(ValueError, match="Parser not set"):
            builder.build()

    def test_build_defaults_to_toon_encoder(self) -> None:
        """Pipeline defaults to TOON encoder if not set."""
        pipeline = PipelineBuilder().with_parser(JsonParser()).build()

        assert isinstance(pipeline.encoder, ToonEncoder)

    def test_with_encoder(self) -> None:
        """with_encoder sets custom encoder."""
        encoder = JsonEncoder(sort_keys=True)
        pipeline = (
            PipelineBuilder().with_parser(JsonParser()).with_encoder(encoder).build()
        )

        assert pipeline.encoder is encoder

    def test_with_auto_parser_from_filename(self, tmp_path: Path) -> None:
        """with_auto_parser detects parser from filename."""
        json_file = tmp_path / "data.json"
        json_file.write_bytes(b'{"test": 1}')

        pipeline = (
            PipelineBuilder()
            .with_auto_parser(filename=json_file)
            .with_format("json")
            .build()
        )

        assert isinstance(pipeline.parser, JsonParser)

    def test_with_auto_parser_from_data(self) -> None:
        """with_auto_parser detects parser from data content."""
        pipeline = (
            PipelineBuilder()
            .with_auto_parser(data=b'{"test": 1}')
            .with_format("json")
            .build()
        )

        result = pipeline.run(b'{"key": "value"}')
        assert result == '{"key":"value"}'

    def test_method_chaining(self) -> None:
        """Builder methods return self for chaining."""
        builder = PipelineBuilder()

        result = builder.with_parser(JsonParser())
        assert result is builder

        result = result.with_format("json")
        assert result is builder

        result = result.with_encoder(JsonEncoder())
        assert result is builder
