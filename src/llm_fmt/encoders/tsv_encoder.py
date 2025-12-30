"""TSV (Tab-Separated Values) encoder.

TSV is a token-efficient format for flat tabular data.
Tabs tokenize more efficiently than commas in most BPE vocabularies,
achieving 40-50% token savings on suitable data.

Format:
    Header row contains column names separated by tabs
    Data rows contain values separated by tabs
    Tabs and newlines in values are escaped
"""

from typing import Any

from llm_fmt.errors import EncodeError


class TsvEncoder:
    """Encoder for TSV format.

    Only supports uniform arrays of objects (flat tabular data).
    """

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to TSV format.

        Args:
            data: Input data - must be a list of dicts with uniform structure.

        Returns:
            TSV-formatted string with header row.

        Raises:
            EncodeError: If data is not a uniform array of objects.
        """
        if not isinstance(data, list):
            msg = "TSV format requires a list of objects"
            raise EncodeError(msg, format_name="tsv")

        if not data:
            return ""

        if not all(isinstance(item, dict) for item in data):
            msg = "TSV format requires all items to be objects"
            raise EncodeError(msg, format_name="tsv")

        # Get headers from first item (assuming uniform structure)
        headers = list(data[0].keys())

        if not headers:
            return ""

        lines = ["\t".join(headers)]

        for item in data:
            values = [self._encode_value(item.get(h, "")) for h in headers]
            lines.append("\t".join(values))

        return "\n".join(lines)

    def _encode_value(self, value: Any) -> str:  # noqa: ANN401
        """Encode a single value for TSV.

        Args:
            value: Value to encode.

        Returns:
            String representation with tabs and newlines escaped.
        """
        if value is None:
            return ""
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return self._escape_tsv(value)
        # For nested structures, convert to string representation
        return self._escape_tsv(str(value))

    def _escape_tsv(self, value: str) -> str:
        r"""Escape tabs and newlines in TSV values.

        Args:
            value: String to escape.

        Returns:
            Escaped string with \t and \n sequences.
        """
        # Escape backslashes first to avoid double-escaping
        return (
            value.replace("\\", "\\\\")
            .replace("\t", "\\t")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )
