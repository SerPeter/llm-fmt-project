"""Exclude filter using dpath patterns."""

import contextlib
import copy
from typing import TYPE_CHECKING, Any

import dpath

if TYPE_CHECKING:
    from collections.abc import Iterator


class ExcludeFilter:
    """Filter that removes paths matching the pattern."""

    def __init__(self, pattern: str) -> None:
        """Initialize exclude filter.

        Args:
            pattern: dpath glob pattern to exclude.
        """
        self.pattern = pattern

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Remove data matching the pattern.

        Args:
            data: Input data (dict or list).

        Returns:
            Data with matching paths removed.
        """
        if not isinstance(data, dict):
            return data

        # Work on a copy to avoid mutating input
        result = copy.deepcopy(data)

        # Collect paths to delete (can't modify during iteration)
        paths_to_delete = [path for path, _ in dpath.search(result, self.pattern, yielded=True)]

        # Delete in reverse order to handle nested paths correctly
        for path in sorted(paths_to_delete, reverse=True):
            # Path may have been deleted as part of parent
            with contextlib.suppress(KeyError):
                dpath.delete(result, path)

        return result

    def apply_stream(self, stream: Iterator[Any]) -> Iterator[Any]:
        """Streaming exclude filter.

        Args:
            stream: Iterator of data items.

        Yields:
            Filtered data items.
        """
        for item in stream:
            yield self(item)
