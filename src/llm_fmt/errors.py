"""Error types and validation utilities."""

from dataclasses import dataclass, field


@dataclass
class ValidationError:
    """A single validation error."""

    location: str
    message: str

    def __str__(self) -> str:
        """Format as location: message."""
        return f"{self.location}: {self.message}"


@dataclass
class ConfigurationError(Exception):
    """Raised when CLI configuration is invalid.

    Collects multiple validation errors to report all issues at once.
    """

    errors: list[ValidationError] = field(default_factory=list)

    def __str__(self) -> str:
        """Format all errors, one per line."""
        return "\n".join(str(e) for e in self.errors)

    def add(self, location: str, message: str) -> ConfigurationError:
        """Add a validation error.

        Args:
            location: Where the error occurred (e.g., "--filter[0]").
            message: Description of the error.

        Returns:
            Self for method chaining.
        """
        self.errors.append(ValidationError(location, message))
        return self

    def __bool__(self) -> bool:
        """True if there are any errors."""
        return len(self.errors) > 0


class ParseError(Exception):
    """Raised when input parsing fails."""

    def __init__(self, message: str, source: str | None = None) -> None:
        """Initialize parse error.

        Args:
            message: Error description.
            source: Optional source identifier (filename, "stdin", etc.).
        """
        self.source = source
        super().__init__(message)

    def __str__(self) -> str:
        """Format with source if available."""
        if self.source:
            return f"{self.source}: {super().__str__()}"
        return super().__str__()


class FilterError(Exception):
    """Raised when a filter operation fails."""


class EncodeError(Exception):
    """Raised when encoding fails."""

    def __init__(self, message: str, format_name: str | None = None) -> None:
        """Initialize encode error.

        Args:
            message: Error description.
            format_name: Optional format that failed.
        """
        self.format_name = format_name
        super().__init__(message)

    def __str__(self) -> str:
        """Format with format name if available."""
        if self.format_name:
            return f"{self.format_name}: {super().__str__()}"
        return super().__str__()


class ConfigError(Exception):
    """Raised when configuration file is invalid or missing."""
