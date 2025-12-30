"""Pipeline runner connecting parsers, filters, and encoders."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from llm_fmt.encoders import Encoder, ToonEncoder, get_encoder
from llm_fmt.errors import EncodeError, ParseError
from llm_fmt.filters import Filter, FilterChain
from llm_fmt.parsers import Parser, detect_parser

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Pipeline:
    """Composable pipeline: parse -> filter -> encode."""

    parser: Parser
    encoder: Encoder
    filters: FilterChain = field(default_factory=FilterChain)

    def run(self, data: bytes) -> str:
        """Run the pipeline on input data.

        Args:
            data: Raw input bytes.

        Returns:
            Encoded output string.

        Raises:
            ParseError: If parsing fails.
            FilterError: If filtering fails.
            EncodeError: If encoding fails.
        """
        try:
            parsed = self.parser.parse(data)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(str(e)) from e

        filtered = self.filters(parsed)

        try:
            return self.encoder.encode(filtered)
        except Exception as e:
            raise EncodeError(str(e)) from e


class PipelineBuilder:
    """Builder for constructing pipelines."""

    def __init__(self) -> None:
        """Initialize builder with defaults."""
        self._parser: Parser | None = None
        self._encoder: Encoder | None = None
        self._filters: list[Filter] = []

    def with_parser(self, parser: Parser) -> PipelineBuilder:
        """Set the parser.

        Args:
            parser: Parser instance.

        Returns:
            Self for method chaining.
        """
        self._parser = parser
        return self

    def with_auto_parser(
        self,
        filename: Path | None = None,
        data: bytes | None = None,
    ) -> PipelineBuilder:
        """Auto-detect and set parser.

        Args:
            filename: Optional filename for extension-based detection.
            data: Optional data for magic-byte detection.

        Returns:
            Self for method chaining.
        """
        self._parser = detect_parser(filename, data)
        return self

    def with_encoder(self, encoder: Encoder) -> PipelineBuilder:
        """Set the encoder.

        Args:
            encoder: Encoder instance.

        Returns:
            Self for method chaining.
        """
        self._encoder = encoder
        return self

    def with_format(
        self,
        format_name: str,
        *,
        sort_keys: bool = False,
    ) -> PipelineBuilder:
        """Set encoder by format name.

        Args:
            format_name: Format name (toon, json, yaml).
            sort_keys: Sort object keys alphabetically (JSON only).

        Returns:
            Self for method chaining.
        """
        self._encoder = get_encoder(format_name, sort_keys=sort_keys)
        return self

    def add_filter(self, f: Filter) -> PipelineBuilder:
        """Add a filter to the chain.

        Args:
            f: Filter to add.

        Returns:
            Self for method chaining.
        """
        self._filters.append(f)
        return self

    def build(self) -> Pipeline:
        """Build the pipeline.

        Returns:
            Configured Pipeline instance.

        Raises:
            ValueError: If parser is not set.
        """
        if self._parser is None:
            msg = "Parser not set. Use with_parser() or with_auto_parser()."
            raise ValueError(msg)

        return Pipeline(
            parser=self._parser,
            encoder=self._encoder or ToonEncoder(),
            filters=FilterChain(self._filters),
        )
