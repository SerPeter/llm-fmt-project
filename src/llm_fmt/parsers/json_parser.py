"""JSON input parser using orjson for performance."""

from typing import Any

import orjson

from llm_fmt.errors import ParseError


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
