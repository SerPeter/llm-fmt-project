"""Input parsers for various data formats."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from llm_fmt.parsers.json_parser import JsonParser
from llm_fmt.parsers.yaml_parser import YamlParser

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

__all__ = ["JsonParser", "Parser", "YamlParser", "detect_parser"]

EXTENSION_MAP: dict[str, type[Parser]] = {
    ".json": JsonParser,
    ".yaml": YamlParser,
    ".yml": YamlParser,
}


@runtime_checkable
class Parser(Protocol):
    """Protocol for input parsers."""

    def parse(self, data: bytes) -> Any:  # noqa: ANN401
        """Parse bytes into Python object.

        Args:
            data: Raw bytes to parse.

        Returns:
            Parsed Python object (dict, list, etc.).
        """
        ...

    def parse_stream(self, stream: Iterator[bytes]) -> Iterator[Any]:
        """Streaming parse (future).

        Args:
            stream: Iterator of byte chunks.

        Yields:
            Parsed Python objects.
        """
        ...


def detect_parser(
    filename: Path | None = None,
    data: bytes | None = None,
) -> Parser:
    """Auto-detect parser from filename extension or magic bytes.

    Args:
        filename: Optional path to determine format from extension.
        data: Optional raw bytes to detect format from content.

    Returns:
        Appropriate parser instance.

    Raises:
        ValueError: If format cannot be detected.
    """
    # Try extension first
    if filename is not None:
        suffix = filename.suffix.lower()
        if suffix in EXTENSION_MAP:
            return EXTENSION_MAP[suffix]()

    # Fall back to magic bytes detection
    if data is not None:
        stripped = data.lstrip()
        if stripped.startswith((b"{", b"[")):
            return JsonParser()
        if stripped.startswith((b"<?xml", b"<")):
            msg = "XML parsing not yet implemented"
            raise NotImplementedError(msg)
        # Default to YAML (superset of JSON)
        return YamlParser()

    msg = "Cannot detect format: no filename or data provided"
    raise ValueError(msg)
