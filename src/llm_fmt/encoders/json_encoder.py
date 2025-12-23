"""Compact JSON encoder.

Produces minified JSON with no whitespace for token efficiency.
Uses orjson for performance.
"""

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from collections.abc import Iterator


class JsonEncoder:
    """Encoder for compact JSON format."""

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to compact JSON.

        Args:
            data: Python object to encode.

        Returns:
            Minified JSON string.
        """
        return orjson.dumps(data).decode()

    def encode_stream(self, stream: Iterator[Any]) -> Iterator[str]:
        """Streaming JSON encode.

        Args:
            stream: Iterator of data items.

        Yields:
            JSON-encoded strings (one per item).

        Note:
            Each item is encoded separately.
            For JSON array streaming, items are yielded as array elements.
        """
        first = True
        yield "["

        for item in stream:
            if not first:
                yield ","
            yield orjson.dumps(item).decode()
            first = False

        yield "]"
