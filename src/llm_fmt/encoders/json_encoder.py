"""Compact JSON encoder.

Produces minified JSON with no whitespace for token efficiency.
Uses orjson for performance.
"""

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from collections.abc import Iterator


class JsonEncoder:
    """Encoder for compact JSON format.

    Args:
        sort_keys: Sort object keys alphabetically for deterministic output.
    """

    def __init__(self, *, sort_keys: bool = False) -> None:
        """Initialize encoder with options.

        Args:
            sort_keys: Sort object keys alphabetically.
        """
        self._sort_keys = sort_keys

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to compact JSON.

        Args:
            data: Python object to encode.

        Returns:
            Minified JSON string.
        """
        opts = orjson.OPT_NON_STR_KEYS
        if self._sort_keys:
            opts |= orjson.OPT_SORT_KEYS
        return orjson.dumps(data, option=opts).decode()

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
        opts = orjson.OPT_NON_STR_KEYS
        if self._sort_keys:
            opts |= orjson.OPT_SORT_KEYS

        first = True
        yield "["

        for item in stream:
            if not first:
                yield ","
            yield orjson.dumps(item, option=opts).decode()
            first = False

        yield "]"
