"""TOON (Tabular Object Notation) encoder.

TOON is a token-efficient format for uniform arrays of objects.
It achieves 30-60% token savings over JSON for suitable data.

Format:
    Header row contains column names separated by |
    Data rows contain values separated by |
    Special values: null, true, false preserved as-is
    Strings containing | or newlines are escaped
"""

from typing import TYPE_CHECKING, Any

import orjson

if TYPE_CHECKING:
    from collections.abc import Iterator


class ToonEncoder:
    """Encoder for TOON format."""

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to TOON format.

        Args:
            data: Input data, ideally a list of uniform dicts.

        Returns:
            TOON-formatted string.

        Raises:
            TypeError: If data is not a list or items are not dicts.
        """
        if not isinstance(data, list):
            msg = "TOON format requires a list of objects"
            raise TypeError(msg)

        if not data:
            return ""

        if not all(isinstance(item, dict) for item in data):
            msg = "TOON format requires all items to be objects"
            raise TypeError(msg)

        # Get all unique keys in order of first appearance
        keys = self._get_ordered_keys(data)

        if not keys:
            return ""

        lines = [self._encode_header(keys)]
        lines.extend(self._encode_row(keys, item) for item in data)

        return "\n".join(lines)

    def _get_ordered_keys(self, data: list[dict[str, Any]]) -> list[str]:
        """Get all unique keys preserving first-appearance order.

        Args:
            data: List of dicts.

        Returns:
            Ordered list of unique keys.
        """
        seen: dict[str, None] = {}
        for item in data:
            for key in item:
                if key not in seen:
                    seen[key] = None
        return list(seen.keys())

    def _encode_header(self, keys: list[str]) -> str:
        """Encode header row.

        Args:
            keys: Column names.

        Returns:
            Header line.
        """
        return "|".join(keys)

    def _encode_row(self, keys: list[str], item: dict[str, Any]) -> str:
        """Encode a data row.

        Args:
            keys: Column names (for ordering).
            item: Dict to encode.

        Returns:
            Data line.
        """
        values = [self._encode_value(item.get(key)) for key in keys]
        return "|".join(values)

    def _encode_value(self, value: Any) -> str:  # noqa: ANN401
        """Encode a single value.

        Args:
            value: Value to encode.

        Returns:
            String representation.
        """
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return self._escape_string(value)
        if isinstance(value, (list, dict)):
            return orjson.dumps(value).decode()
        return str(value)

    def _escape_string(self, s: str) -> str:
        """Escape string for TOON format.

        Args:
            s: String to escape.

        Returns:
            Escaped string.
        """
        # Escape pipe and newline characters
        if "|" in s or "\n" in s or "\r" in s:
            s = s.replace("\\", "\\\\")
            s = s.replace("|", "\\|")
            s = s.replace("\n", "\\n")
            s = s.replace("\r", "\\r")
        return s

    def encode_stream(self, stream: Iterator[Any]) -> Iterator[str]:
        """Streaming TOON encode.

        Args:
            stream: Iterator of data items (should be list of dicts).

        Yields:
            TOON-formatted lines.

        Note:
            For streaming, assumes first item determines the schema.
        """
        first = True
        keys: list[str] = []

        for stream_item in stream:
            items = stream_item if isinstance(stream_item, list) else [stream_item]

            for record in items:
                if not isinstance(record, dict):
                    continue

                if first:
                    keys = list(record.keys())
                    yield self._encode_header(keys)
                    first = False

                yield self._encode_row(keys, record)
