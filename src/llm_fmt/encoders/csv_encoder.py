"""CSV (Comma-Separated Values) encoder.

CSV is a widely-supported format for flat tabular data.
While slightly less token-efficient than TSV (commas vs tabs),
CSV is more universally readable and importable.

Format:
    Header row contains column names separated by commas
    Data rows contain values separated by commas
    Values containing commas, quotes, or newlines are quoted
"""

import csv
import io
from typing import Any

from llm_fmt.errors import EncodeError


class CsvEncoder:
    """Encoder for CSV format.

    Only supports uniform arrays of objects (flat tabular data).
    """

    def encode(self, data: Any) -> str:  # noqa: ANN401
        """Encode data to CSV format.

        Args:
            data: Input data - must be a list of dicts with uniform structure.

        Returns:
            CSV-formatted string with header row.

        Raises:
            EncodeError: If data is not a uniform array of objects.
        """
        if not isinstance(data, list):
            msg = "CSV format requires a list of objects"
            raise EncodeError(msg, format_name="csv")

        if not data:
            return ""

        if not all(isinstance(item, dict) for item in data):
            msg = "CSV format requires all items to be objects"
            raise EncodeError(msg, format_name="csv")

        # Get headers from first item (assuming uniform structure)
        headers = list(data[0].keys())

        if not headers:
            return ""

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header
        writer.writerow(headers)

        # Write data rows
        for item in data:
            row = [self._encode_value(item.get(h, "")) for h in headers]
            writer.writerow(row)

        return output.getvalue()

    def _encode_value(self, value: Any) -> str:  # noqa: ANN401
        """Encode a single value for CSV.

        Args:
            value: Value to encode.

        Returns:
            String representation.
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
            return value
        # For nested structures, convert to string representation
        return str(value)
