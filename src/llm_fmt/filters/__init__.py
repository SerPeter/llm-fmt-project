"""Data filters for transformation pipeline."""

from typing import Any, Protocol, runtime_checkable

from llm_fmt.filters.depth import MaxDepthFilter
from llm_fmt.filters.include import IncludeFilter

__all__ = ["Filter", "FilterChain", "IncludeFilter", "MaxDepthFilter"]


@runtime_checkable
class Filter(Protocol):
    """Protocol for data filters."""

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Transform data (callable interface).

        Args:
            data: Input data to filter.

        Returns:
            Filtered/transformed data.
        """
        ...


class FilterChain:
    """Chain of filters applied in sequence."""

    def __init__(self, filters: list[Filter] | None = None) -> None:
        """Initialize filter chain.

        Args:
            filters: List of filters to apply in order.
        """
        self.filters: list[Filter] = filters or []

    def add(self, f: Filter) -> FilterChain:
        """Add a filter to the chain.

        Args:
            f: Filter to add.

        Returns:
            Self for method chaining.
        """
        self.filters.append(f)
        return self

    def __call__(self, data: Any) -> Any:  # noqa: ANN401
        """Apply all filters in sequence (callable interface).

        Args:
            data: Input data.

        Returns:
            Data after all filters applied.
        """
        for f in self.filters:
            data = f(data)
        return data

    def __len__(self) -> int:
        """Return number of filters in chain."""
        return len(self.filters)
