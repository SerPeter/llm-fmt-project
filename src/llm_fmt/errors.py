"""Error types and validation utilities.

Exit codes:
    0: Success
    1: General error (encoding, format, runtime errors)
    2: Input error (file not found, parse error, invalid input)
"""

from dataclasses import dataclass, field


class LLMFmtError(Exception):
    """Base exception for llm-fmt.

    All llm-fmt exceptions should inherit from this class.
    The exit_code attribute determines the CLI exit code.
    """

    exit_code: int = 1


@dataclass
class ValidationError:
    """A single validation error."""

    location: str
    message: str

    def __str__(self) -> str:
        """Format as location: message."""
        return f"{self.location}: {self.message}"


@dataclass
class ConfigurationError(LLMFmtError):
    """Raised when CLI configuration is invalid.

    Collects multiple validation errors to report all issues at once.
    """

    errors: list[ValidationError] = field(default_factory=list)
    exit_code: int = field(default=2, init=False)

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


class ParseError(LLMFmtError):
    """Raised when input parsing fails."""

    exit_code = 2

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


class FilterError(LLMFmtError):
    """Raised when a filter operation fails."""

    exit_code = 1


class EncodeError(LLMFmtError):
    """Raised when encoding fails."""

    exit_code = 1

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


class ConfigError(LLMFmtError):
    """Raised when configuration file is invalid or missing."""

    exit_code = 2


class InputError(LLMFmtError):
    """Raised when input file cannot be read (file not found, permission denied)."""

    exit_code = 2


class OutputError(LLMFmtError):
    """Raised when output cannot be written."""

    exit_code = 1
