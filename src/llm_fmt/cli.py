"""CLI entry point for llm-fmt."""

import sys
from pathlib import Path

import click

from llm_fmt import __version__

# Import the Rust native module
try:
    from llm_fmt._native import convert as rust_convert, is_available, version as rust_version
    RUST_AVAILABLE = is_available()
except ImportError:
    RUST_AVAILABLE = False
    rust_convert = None
    rust_version = lambda: "N/A"


@click.command()
@click.version_option(version=__version__, prog_name="llm-fmt")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["toon", "json", "yaml", "tsv", "csv"]),
    default="toon",
    help="Output format (default: toon).",
)
@click.option(
    "--input-format",
    "-F",
    "input_format",
    type=click.Choice(["json", "yaml", "xml", "csv", "tsv", "auto"]),
    default="auto",
    help="Input format (default: auto-detect).",
)
@click.option(
    "--filter",
    "-i",
    "include_pattern",
    default=None,
    help="Path expression to extract data (e.g., users[*].name).",
)
@click.option(
    "--max-depth",
    "-d",
    "max_depth",
    type=int,
    default=None,
    help="Maximum depth to traverse.",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Output file (default: stdout).",
)
@click.option(
    "--sort-keys",
    is_flag=True,
    help="Sort object keys alphabetically (JSON format only).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Show full traceback on errors.",
)
@click.argument(
    "input_file",
    type=click.Path(path_type=Path),
    required=False,
)
def main(
    output_format: str,
    input_format: str,
    include_pattern: str | None,
    max_depth: int | None,
    output_file: Path | None,
    sort_keys: bool,
    debug: bool,
    input_file: Path | None,
) -> None:
    """Convert JSON/YAML/XML/CSV to token-efficient formats for LLM contexts.

    Supports TOON, compact JSON, YAML, TSV, and CSV output formats.
    Reduces token consumption by 30-60% when passing structured data to LLMs.

    \b
    Examples:
        llm-fmt data.json                    # Convert to TOON (default)
        llm-fmt -f yaml data.json            # Convert to YAML
        llm-fmt -f tsv data.json             # Convert to TSV
        llm-fmt -i "users[*].name" data.json # Extract user names
        cat data.json | llm-fmt              # Read from stdin
    """
    if not RUST_AVAILABLE:
        click.echo("Error: Rust native module not available. Please reinstall llm-fmt.", err=True)
        sys.exit(1)

    try:
        # Read input
        if input_file is None:
            if sys.stdin.isatty():
                click.echo(click.get_current_context().get_help())
                sys.exit(0)
            data = sys.stdin.buffer.read()
        else:
            if not input_file.exists():
                click.echo(f"Error: File not found: {input_file}", err=True)
                sys.exit(1)
            data = input_file.read_bytes()

        # Call Rust convert function
        result = rust_convert(
            data,
            format=output_format,
            input_format=input_format,
            max_depth=max_depth,
            sort_keys=sort_keys,
            include=include_pattern,
        )

        # Output
        if output_file:
            output_file.write_text(result, encoding="utf-8")
            click.echo(f"Written to {output_file}", err=True)
        else:
            click.echo(result, nl=False)

    except ValueError as e:
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        if debug:
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
