"""YAML input parser."""

from typing import Any

import yaml


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
