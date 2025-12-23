"""JSON input parser using orjson for performance."""

from typing import TYPE_CHECKING, Any

import orjson

from llm_fmt.errors import ParseError

if TYPE_CHECKING:
    from collections.abc import Iterator


class JsonParser:
    """Parser for JSON input data."""

    def parse(self, data: bytes) -> Any:  # noqa: ANN401
        """Parse JSON bytes into Python object.

        Args:
            data: Raw JSON bytes.

        Returns:
            Parsed Python object.

        Raises:
            ParseError: If JSON is invalid.
        """
        try:
            return orjson.loads(data)
        except orjson.JSONDecodeError as e:
            msg = f"Invalid JSON: {e}"
            raise ParseError(msg) from e

    def parse_stream(self, stream: Iterator[bytes]) -> Iterator[Any]:
        """Streaming JSON parse (future).

        Args:
            stream: Iterator of byte chunks.

        Yields:
            Parsed Python objects.

        Note:
            Current implementation buffers all chunks.
            Future: implement true streaming for JSON arrays.
        """
        # Simple implementation: buffer and parse
        # Future: use ijson or similar for true streaming
        buffer = b"".join(stream)
        yield self.parse(buffer)
