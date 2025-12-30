"""XML input parser using xmltodict."""

from typing import Any

import xmltodict

from llm_fmt.errors import ParseError


class XmlParser:
    """Parser for XML input data.

    Converts XML to Python dicts using xmltodict.
    """

    def __init__(self, *, strip_namespace: bool = True) -> None:
        """Initialize XML parser.

        Args:
            strip_namespace: Remove namespace prefixes from tag names.
        """
        self.strip_namespace = strip_namespace

    def parse(self, data: bytes) -> Any:  # noqa: ANN401
        """Parse XML bytes into Python object.

        Args:
            data: Raw XML bytes.

        Returns:
            Parsed Python object (typically a dict).

        Raises:
            ParseError: If XML is invalid.
        """
        try:
            text = data.decode("utf-8")
            return xmltodict.parse(
                text,
                process_namespaces=self.strip_namespace,
                namespaces={} if self.strip_namespace else None,
            )
        except Exception as e:
            msg = f"Invalid XML: {e}"
            raise ParseError(msg) from e
