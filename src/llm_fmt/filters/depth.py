"""Max depth filter for limiting data nesting."""

import copy
from typing import Any


class MaxDepthFilter:
    """Filter that truncates data beyond a specified depth."""

    def __init__(self, max_depth: int) -> None:
        """Initialize max depth filter.

        Args:
            max_depth: Maximum nesting depth to keep (0 = root only).
        """
        if max_depth < 0:
            msg = "max_depth must be non-negative"
            raise ValueError(msg)
        self.max_depth = max_depth

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Truncate data beyond max depth.

        Args:
            data: Input data.

        Returns:
            Data truncated to max depth.
        """
        return self._truncate(copy.deepcopy(data), 0)

    def _truncate(self, data: Any, current_depth: int) -> Any:  # noqa: ANN401
        """Recursively truncate data.

        Args:
            data: Current data node.
            current_depth: Current nesting level.

        Returns:
            Truncated data.
        """
        if current_depth >= self.max_depth:
            if isinstance(data, dict):
                return {k: self._placeholder(v) for k, v in data.items()}
            if isinstance(data, list):
                return [self._placeholder(v) for v in data]
            return data

        if isinstance(data, dict):
            return {k: self._truncate(v, current_depth + 1) for k, v in data.items()}
        if isinstance(data, list):
            return [self._truncate(v, current_depth + 1) for v in data]
        return data

    def _placeholder(self, value: Any) -> Any:  # noqa: ANN401
        """Create placeholder for truncated values.

        Args:
            value: Original value being truncated.

        Returns:
            Placeholder indicating truncation.
        """
        if isinstance(value, dict):
            return {"...": f"{len(value)} keys"}
        if isinstance(value, list):
            return [f"... {len(value)} items"]
        return value
