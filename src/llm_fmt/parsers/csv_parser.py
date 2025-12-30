"""CSV input parser using Python's csv module."""

import csv
import io
from typing import Any

from llm_fmt.errors import ParseError


class CsvParser:
    """Parser for CSV input data.

    Converts CSV to a list of dicts (one per row).
    The first row is used as header names.
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        has_header: bool = True,
    ) -> None:
        """Initialize CSV parser.

        Args:
            delimiter: Field delimiter character.
            has_header: Whether the first row contains headers.
        """
        self.delimiter = delimiter
        self.has_header = has_header

    def parse(self, data: bytes) -> Any:  # noqa: ANN401
        """Parse CSV bytes into Python object.

        Args:
            data: Raw CSV bytes.

        Returns:
            List of dicts if has_header=True, else list of lists.

        Raises:
            ParseError: If CSV is invalid.
        """
        try:
            text = data.decode("utf-8")
            reader = csv.reader(io.StringIO(text), delimiter=self.delimiter)
            rows = list(reader)
        except csv.Error as e:
            msg = f"Invalid CSV: {e}"
            raise ParseError(msg) from e
        except UnicodeDecodeError as e:
            msg = f"Invalid CSV encoding: {e}"
            raise ParseError(msg) from e

        if not rows:
            return []

        if self.has_header:
            headers = rows[0]
            return [dict(zip(headers, row, strict=False)) for row in rows[1:]]
        return rows
