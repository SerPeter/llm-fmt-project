"""TOON (Tabular Object Notation) encoder.

TOON is a token-efficient format for uniform arrays of objects.
It achieves 30-60% token savings over JSON for suitable data.

Format:
    Header row contains column names separated by |
    Data rows contain values separated by |
    Special values: null, true, false preserved as-is
    Strings containing | or newlines are escaped
    Nested structures are JSON-encoded inline
"""

from typing import Any

import orjson

from llm_fmt.errors import EncodeError


class ToonEncoder:
    """Encoder for TOON format."""

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to TOON format.

        Args:
            data: Input data - dict, list of dicts, or list of primitives.

        Returns:
            TOON-formatted string.

        Raises:
            EncodeError: If data structure is not supported.
        """
        if isinstance(data, dict):
            return self._encode_single_object(data)

        if isinstance(data, list):
            return self._encode_list(data)

        # Primitives
        return self._encode_value(data)

    def _encode_single_object(self, obj: dict[str, Any]) -> str:
        """Encode a single object as header + single row.

        Args:
            obj: Dictionary to encode.

        Returns:
            TOON-formatted string with header and one data row.
        """
        if not obj:
            return ""

        keys = list(obj.keys())
        header = self._encode_header(keys)
        row = self._encode_row(keys, obj)
        return f"{header}\n{row}"

    def _encode_list(self, data: list[Any]) -> str:
        """Encode a list to TOON format.

        Args:
            data: List to encode.

        Returns:
            TOON-formatted string.

        Raises:
            EncodeError: If list contains unsupported types.
        """
        if not data:
            return ""

        # Check if all items are dicts
        if all(isinstance(item, dict) for item in data):
            return self._encode_object_array(data)

        # List of primitives - one per line
        if all(not isinstance(item, (dict, list)) for item in data):
            return "\n".join(self._encode_value(item) for item in data)

        # Mixed or nested lists - encode each item
        msg = "TOON format does not support mixed arrays of objects and primitives"
        raise EncodeError(msg)

    def _encode_object_array(self, data: list[dict[str, Any]]) -> str:
        """Encode array of objects in tabular format.

        Args:
            data: List of dictionaries.

        Returns:
            TOON-formatted string with header and data rows.
        """
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
        r"""Escape string for TOON format.

        Escapes:
            - Backslashes: \\ -> \\\\
            - Pipes: | -> \\|
            - Newlines: \\n, \\r

        Args:
            s: String to escape.

        Returns:
            Escaped string.
        """
        needs_escape = "|" in s or "\n" in s or "\r" in s or "\\" in s
        if needs_escape:
            # Order matters: escape backslashes first
            s = s.replace("\\", "\\\\")
            s = s.replace("|", "\\|")
            s = s.replace("\n", "\\n")
            s = s.replace("\r", "\\r")
        return s
