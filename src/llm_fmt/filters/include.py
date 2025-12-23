"""Include filter using dpath patterns."""

from typing import TYPE_CHECKING, Any

import dpath

if TYPE_CHECKING:
    from collections.abc import Iterator


class IncludeFilter:
    """Filter that keeps only paths matching the pattern."""

    def __init__(self, pattern: str) -> None:
        """Initialize include filter.

        Args:
            pattern: dpath glob pattern to include.
        """
        self.pattern = pattern

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Keep only data matching the pattern.

        Args:
            data: Input data (dict or list).

        Returns:
            Filtered data containing only matching paths.
        """
        if not isinstance(data, dict):
            # For non-dict data, return as-is if pattern matches root
            if self.pattern in ("*", "**"):
                return data
            return None

        result: dict[str, Any] = {}
        for path, value in dpath.search(data, self.pattern, yielded=True):
            dpath.new(result, path, value)
        return result

    def apply_stream(self, stream: Iterator[Any]) -> Iterator[Any]:
        """Streaming include filter.

        Args:
            stream: Iterator of data items.

        Yields:
            Filtered data items.
        """
        for item in stream:
            result = self(item)
            if result is not None:
                yield result
