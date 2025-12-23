"""YAML encoder.

Produces clean YAML output for human-readable token-efficient format.
Uses block style for readability and literal block style for multi-line strings.
"""

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator


class _CleanYamlDumper(yaml.SafeDumper):
    """Custom dumper that produces clean, minimal YAML.

    Features:
        - Literal block style (|) for multi-line strings
        - Minimal quoting
        - No line wrapping
    """


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Use literal block style for multi-line strings.

    Args:
        dumper: YAML dumper instance.
        data: String to represent.

    Returns:
        YAML scalar node.
    """
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_CleanYamlDumper.add_representer(str, _str_representer)


class YamlEncoder:
    """Encoder for YAML format.

    Args:
        indent: Indentation width (default 2).
    """

    def __init__(self, *, indent: int = 2) -> None:
        """Initialize encoder with options.

        Args:
            indent: Indentation width.
        """
        self._indent = indent

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to YAML.

        Args:
            data: Python object to encode.

        Returns:
            YAML-formatted string.
        """
        return yaml.dump(
            data,
            Dumper=_CleanYamlDumper,
            default_flow_style=False,
            indent=self._indent,
            allow_unicode=True,
            sort_keys=False,
            width=1000,  # Prevent line wrapping
        )

    def encode_stream(self, stream: Iterator[Any]) -> Iterator[str]:
        """Streaming YAML encode.

        Args:
            stream: Iterator of data items.

        Yields:
            YAML-encoded strings (one document per item).
        """
        for item in stream:
            yield "---\n"
            yield yaml.dump(
                item,
                Dumper=_CleanYamlDumper,
                default_flow_style=False,
                indent=self._indent,
                allow_unicode=True,
                sort_keys=False,
                width=1000,
            )
