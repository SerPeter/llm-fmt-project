"""Compact JSON encoder.

Produces minified JSON with no whitespace for token efficiency.
Uses orjson for performance.
"""

from typing import Any

import orjson


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
