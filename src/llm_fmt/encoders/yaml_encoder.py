"""YAML encoder.

Produces clean YAML output for human-readable token-efficient format.
"""

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator


class YamlEncoder:
    """Encoder for YAML format."""

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to YAML.

        Args:
            data: Python object to encode.

        Returns:
            YAML-formatted string.
        """
        return yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
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
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
