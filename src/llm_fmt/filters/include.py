"""Include filter using JMESPath expressions."""

from typing import TYPE_CHECKING, Any

import jmespath
from jmespath.exceptions import JMESPathError

if TYPE_CHECKING:
    from collections.abc import Iterator


class IncludeFilter:
    """Filter that extracts data matching JMESPath expression."""

    def __init__(self, expression: str) -> None:
        """Initialize include filter.

        Args:
            expression: JMESPath expression to match.

        Raises:
            ValueError: If expression is invalid.
        """
        try:
            self._compiled = jmespath.compile(expression)
        except JMESPathError as e:
            msg = f"Invalid JMESPath expression '{expression}': {e}"
            raise ValueError(msg) from e
        self.expression = expression

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Extract data matching the expression.

        Args:
            data: Input data (dict or list).

        Returns:
            Extracted data matching expression, or original data if no match.
        """
        result = self._compiled.search(data)
        # Return original data if expression matches nothing
        return result if result is not None else data

    def apply_stream(self, stream: Iterator[Any]) -> Iterator[Any]:
        """Streaming include filter.

        Args:
            stream: Iterator of data items.

        Yields:
            Filtered data items (skips None results).
        """
        for item in stream:
            result = self._compiled.search(item)
            if result is not None:
                yield result
