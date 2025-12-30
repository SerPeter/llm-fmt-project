"""Output encoders for various formats."""

from typing import Any, Protocol, runtime_checkable

from llm_fmt.encoders.csv_encoder import CsvEncoder
from llm_fmt.encoders.json_encoder import JsonEncoder
from llm_fmt.encoders.toon import ToonEncoder
from llm_fmt.encoders.tsv_encoder import TsvEncoder
from llm_fmt.encoders.yaml_encoder import YamlEncoder

__all__ = [
    "CsvEncoder",
    "Encoder",
    "JsonEncoder",
    "ToonEncoder",
    "TsvEncoder",
    "YamlEncoder",
    "get_encoder",
]

ENCODER_MAP: dict[str, type[Encoder]] = {
    "toon": ToonEncoder,
    "json": JsonEncoder,
    "yaml": YamlEncoder,
    "tsv": TsvEncoder,
    "csv": CsvEncoder,
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


def get_encoder(format_name: str, *, sort_keys: bool = False) -> Encoder:
    """Get encoder by format name.

    Args:
        format_name: Name of the output format.
        sort_keys: Sort object keys alphabetically (JSON only).

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

    if format_lower == "json":
        return JsonEncoder(sort_keys=sort_keys)
    return ENCODER_MAP[format_lower]()
