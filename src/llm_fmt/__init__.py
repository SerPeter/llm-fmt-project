"""llm-fmt: Token-efficient data format converter for LLM contexts."""

__version__ = "0.1.0"

# Re-export from Rust native module
try:
    from llm_fmt._native import (
        analyze,
        convert,
        detect_shape,
        is_available,
        select_format,
        version as native_version,
    )

    RUST_AVAILABLE = is_available()
except ImportError:
    RUST_AVAILABLE = False

    def convert(*args, **kwargs):  # noqa: ARG001
        """Placeholder when Rust module unavailable."""
        raise ImportError("Rust native module not available. Please reinstall llm-fmt.")

    def analyze(*args, **kwargs):  # noqa: ARG001
        """Placeholder when Rust module unavailable."""
        raise ImportError("Rust native module not available. Please reinstall llm-fmt.")

    def detect_shape(*args, **kwargs):  # noqa: ARG001
        """Placeholder when Rust module unavailable."""
        raise ImportError("Rust native module not available. Please reinstall llm-fmt.")

    def select_format(*args, **kwargs):  # noqa: ARG001
        """Placeholder when Rust module unavailable."""
        raise ImportError("Rust native module not available. Please reinstall llm-fmt.")

    def native_version():
        """Placeholder when Rust module unavailable."""
        return "N/A"


__all__ = [
    "__version__",
    "analyze",
    "convert",
    "detect_shape",
    "RUST_AVAILABLE",
    "native_version",
    "select_format",
]
