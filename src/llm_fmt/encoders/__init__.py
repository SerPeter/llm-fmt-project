"""Output encoders for various formats."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from llm_fmt.encoders.json_encoder import JsonEncoder
from llm_fmt.encoders.toon import ToonEncoder
from llm_fmt.encoders.yaml_encoder import YamlEncoder

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["Encoder", "JsonEncoder", "ToonEncoder", "YamlEncoder", "get_encoder"]

ENCODER_MAP: dict[str, type[Encoder]] = {
    "toon": ToonEncoder,
    "json": JsonEncoder,
    "yaml": YamlEncoder,
}


@runtime_checkable
class Encoder(Protocol):
    """Protocol for output encoders."""

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to output format.

        Args:
            data: Python object to encode.

        Returns:
            Formatted string output.
        """
        ...

    def encode_stream(self, stream: Iterator[Any]) -> Iterator[str]:
        """Streaming encode (future).

        Args:
            stream: Iterator of data items.

        Yields:
            Encoded string chunks.
        """
        ...


def get_encoder(format_name: str) -> Encoder:
    """Get encoder by format name.

    Args:
        format_name: Name of the output format.

    Returns:
        Encoder instance.

    Raises:
        ValueError: If format is not supported.
    """
    format_lower = format_name.lower()
    if format_lower not in ENCODER_MAP:
        supported = ", ".join(sorted(ENCODER_MAP.keys()))
        msg = f"Unsupported format: {format_name}. Supported: {supported}"
        raise ValueError(msg)
    return ENCODER_MAP[format_lower]()
