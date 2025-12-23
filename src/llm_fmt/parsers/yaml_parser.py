"""YAML input parser."""

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator


class YamlParser:
    """Parser for YAML input data."""

    def parse(self, data: bytes) -> Any:  # noqa: ANN401
        """Parse YAML bytes into Python object.

        Args:
            data: Raw YAML bytes.

        Returns:
            Parsed Python object.

        Raises:
            yaml.YAMLError: If YAML is invalid.
        """
        return yaml.safe_load(data)

    def parse_stream(self, stream: Iterator[bytes]) -> Iterator[Any]:
        """Streaming YAML parse (future).

        Args:
            stream: Iterator of byte chunks.

        Yields:
            Parsed Python objects (one per YAML document).

        Note:
            Current implementation buffers all chunks.
            Future: implement true streaming for multi-document YAML.
        """
        buffer = b"".join(stream)
        # YAML supports multiple documents separated by ---
        yield from yaml.safe_load_all(buffer)
