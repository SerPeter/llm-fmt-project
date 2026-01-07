"""llm-fmt: Token-efficient data format converter for LLM contexts."""

from typing import Any, NoReturn

__version__ = "0.1.0"

# Export configuration
from llm_fmt.config import Config, load_config

_RUST_UNAVAILABLE_MSG = "Rust native module not available. Please reinstall llm-fmt."

# Re-export from Rust native module
try:
    from llm_fmt._native import (
        analyze,
        convert,
        detect_shape,
        is_available,
        select_format,
    )
    from llm_fmt._native import (
        version as native_version,
    )

    RUST_AVAILABLE = is_available()
except ImportError:
    RUST_AVAILABLE = False

    def convert(*_args: Any, **_kwargs: Any) -> NoReturn:
        """Placeholder when Rust module unavailable."""
        raise ImportError(_RUST_UNAVAILABLE_MSG)

    def analyze(*_args: Any, **_kwargs: Any) -> NoReturn:
        """Placeholder when Rust module unavailable."""
        raise ImportError(_RUST_UNAVAILABLE_MSG)

    def detect_shape(*_args: Any, **_kwargs: Any) -> NoReturn:
        """Placeholder when Rust module unavailable."""
        raise ImportError(_RUST_UNAVAILABLE_MSG)

    def select_format(*_args: Any, **_kwargs: Any) -> NoReturn:
        """Placeholder when Rust module unavailable."""
        raise ImportError(_RUST_UNAVAILABLE_MSG)

    def native_version() -> str:
        """Placeholder when Rust module unavailable."""
        return "N/A"


__all__ = [
    "Config",
    "RUST_AVAILABLE",
    "__version__",
    "analyze",
    "convert",
    "detect_shape",
    "load_config",
    "native_version",
    "select_format",
]
