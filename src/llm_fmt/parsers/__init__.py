"""Input parsers for various data formats."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from llm_fmt.parsers.csv_parser import CsvParser
from llm_fmt.parsers.json_parser import JsonParser
from llm_fmt.parsers.xml_parser import XmlParser
from llm_fmt.parsers.yaml_parser import YamlParser

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["CsvParser", "JsonParser", "Parser", "XmlParser", "YamlParser", "detect_parser"]

EXTENSION_MAP: dict[str, type[Parser]] = {
    ".json": JsonParser,
    ".yaml": YamlParser,
    ".yml": YamlParser,
    ".xml": XmlParser,
    ".csv": CsvParser,
    ".tsv": CsvParser,  # TSV is CSV with tab delimiter - handled via auto-detect
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
        if suffix == ".tsv":
            return CsvParser(delimiter="\t")
        if suffix in EXTENSION_MAP:
            return EXTENSION_MAP[suffix]()

    # Fall back to magic bytes detection
    if data is not None:
        stripped = data.lstrip()
        if stripped.startswith((b"{", b"[")):
            return JsonParser()
        if stripped.startswith((b"<?xml", b"<")):
            return XmlParser()
        # Default to YAML (superset of JSON)
        return YamlParser()

    msg = "Cannot detect format: no filename or data provided"
    raise ValueError(msg)
